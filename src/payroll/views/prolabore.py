from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from decimal import Decimal

from ..models.prolabore import ProLaboreSimulation
from ..serializers.prolabore import (
    ProLaboreCalculoSerializer, 
    ProLaboreSimulationSerializer
)
from ...finance.models.dinheiro import Transaction
from ...expenses.models.expenses import Expense, ParcelaDespesa
from ..utils.calculo import calcular_pro_labore_escritorio
from django.core.cache import cache
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin
from ...users.utils.cache_utils import invalidar_cache_prolabore


class ProLaboreViewSet(FirmMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProLaboreSimulationSerializer

    COMPARISON_TOLERANCE = Decimal("0.10")

    def get_queryset(self):
        return ProLaboreSimulation.objects.filter(user=self.request.user)

    def _build_comparison(self, paid_amount: Decimal, suggested_amount: Decimal | None):
        paid = Decimal(paid_amount or 0)
        if not suggested_amount or suggested_amount <= 0:
            return {
                "status": "SEM_REFERENCIA",
                "difference": float(paid),
                "difference_percentage": None,
            }

        diff = paid - suggested_amount
        diff_percentage = diff / suggested_amount

        if diff_percentage > self.COMPARISON_TOLERANCE:
            status_label = "ACIMA_DO_SUGERIDO"
        elif diff_percentage < -self.COMPARISON_TOLERANCE:
            status_label = "ABAIXO_DO_SUGERIDO"
        else:
            status_label = "ALINHADO_AO_SUGERIDO"

        return {
            "status": status_label,
            "difference": float(diff.quantize(Decimal("0.01"))),
            "difference_percentage": round(float(diff_percentage * Decimal("100")), 2),
        }

    def _build_history_payload(self, request):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError({"detail": "O usuário autenticado não possui empresa vinculada."})

        try:
            months = int(request.query_params.get("months", 12))
        except ValueError:
            raise ValidationError({"detail": "O parâmetro 'months' deve ser um inteiro válido."})

        months = max(1, min(months, 36))

        today = timezone.localdate()
        start_reference = today.replace(day=1)
        month_offset = months - 1
        start_month = start_reference.month - month_offset
        start_year = start_reference.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1

        first_day = start_reference.replace(year=start_year, month=start_month)

        payroll_categories_filter = Q(expense__category=Expense.Category.PESSOAL_E_REMUNERACAO) | Q(
            expense__category=Expense.Category.PESSOAS
        )

        monthly_paid = (
            ParcelaDespesa.objects.filter(
                expense__firm_id=firm_id,
                expense__is_active=True,
                is_paid=True,
                paid_at__isnull=False,
                paid_at__gte=first_day,
            )
            .filter(payroll_categories_filter)
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(total_paid=Sum("amount"))
            .order_by("month")
        )

        latest_simulation = self.get_queryset().first()
        suggested_amount = latest_simulation.pro_labore_sugerido if latest_simulation else None

        history = []
        for item in monthly_paid:
            paid_amount = item["total_paid"] or Decimal("0")
            history.append(
                {
                    "month": item["month"].strftime("%Y-%m"),
                    "amount_paid": float(Decimal(paid_amount).quantize(Decimal("0.01"))),
                    "comparison": self._build_comparison(Decimal(paid_amount), suggested_amount),
                }
            )

        total_paid = sum((Decimal(str(row["amount_paid"])) for row in history), Decimal("0"))
        months_with_payment = len(history) or 1
        average_paid = (total_paid / months_with_payment).quantize(Decimal("0.01")) if history else Decimal("0.00")
        last_paid = Decimal(str(history[-1]["amount_paid"])) if history else Decimal("0.00")
        summary_comparison = self._build_comparison(last_paid, suggested_amount)

        track_event(
            user=request.user,
            event_name="pro_labore_historico_visualizado",
            properties={
                "months_window": months,
                "months_with_payment": len(history),
                "latest_suggested_available": bool(suggested_amount),
            },
        )

        return {
            "months_window": months,
            "latest_suggested_pro_labore": float(suggested_amount) if suggested_amount is not None else None,
            "monthly_history": history,
            "summary": {
                "total_paid": float(total_paid.quantize(Decimal("0.01"))),
                "average_paid": float(average_paid),
                "last_paid": float(last_paid.quantize(Decimal("0.01"))),
                "comparison": summary_comparison,
            },
        }

    def list(self, request, *args, **kwargs):
        months = request.query_params.get("months", 12)
        cache_key = f"prolabore_history:{request.user.id}:{months}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached["monthly_history"], status=status.HTTP_200_OK)

        payload = self._build_history_payload(request)
        cache.set(cache_key, payload, timeout=600)
        return Response(payload["monthly_history"], status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, "profile", None)
        
        if not profile:
            track_event(
                user=user,
                event_name="pro_labore_calculo_falha",
                properties={"motivo_erro": "perfil_advogado_nao_encontrado"}
            )
            return Response(
                {"detail": "Perfil de advogado não encontrado para realizar o cálculo."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        firm_id = self._get_firm_id()
        if not firm_id:
            return Response(
                {"detail": "O usuário não possui nenhuma empresa vinculada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        firm_transactions = Transaction.objects.filter(account__firm_id=firm_id)

        calculos_objeto = calcular_pro_labore_escritorio(
            user=user,
            transactions_queryset=firm_transactions,
            tax_regime=profile.tax_regime
        )

        with db_transaction.atomic():
            ProLaboreSimulation.objects.create(
                user=user,
                perfil_estagio=calculos_objeto["nivel_recomendado"].upper(),
                base_disponivel=calculos_objeto["base_disponivel"],
                coef_variacao=calculos_objeto["coef_variacao"],
                meses_analisados=calculos_objeto["meses_analisados"],
                pro_labore_sugerido=calculos_objeto["maximo_seguro"]["pro_labore_bruto"],
                custo_total_escritorio=calculos_objeto["maximo_seguro"]["custo_total_escritorio"]
            )
        invalidar_cache_prolabore(user.id)

        track_event(
            user=user,
            event_name="pro_labore_calculo_sucesso",
            properties={
                "perfil_estagio_recomendado": calculos_objeto["nivel_recomendado"].upper(),
                "meses_analisados": calculos_objeto["meses_analisados"],
                "pro_labore_sugerido": float(calculos_objeto["maximo_seguro"]["pro_labore_bruto"]),
                "tax_regime_utilizado": profile.tax_regime if hasattr(profile, 'tax_regime') else "N/A"
            }
        )

        output_serializer = ProLaboreCalculoSerializer(data=calculos_objeto)
        output_serializer.is_valid(raise_exception=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        months = request.query_params.get("months", 12)
        cache_key = f"prolabore_history:{request.user.id}:{months}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        payload = self._build_history_payload(request)
        cache.set(cache_key, payload, timeout=600)
        return Response(payload, status=status.HTTP_200_OK)