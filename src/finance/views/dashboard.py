from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Case, When, DecimalField
from django.utils import timezone
from django.core.cache import cache
import datetime

from ...fees.models.honorarios import ParcelaHonorario
from ...expenses.models.expenses import ParcelaDespesa
from ...other_income.models.outras_entradas import OutraEntradaInstallment
from ..models.dinheiro import BankAccount
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin


class FinanceDashboardSummaryView(FirmMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        firm_id = self._get_firm_id()

        if not firm_id:
            return Response(
                {"detail": "Usuário não vinculado a nenhuma empresa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hoje = timezone.localdate()
        try:
            year = int(request.query_params.get("year", hoje.year))
            month = int(request.query_params.get("month", hoje.month))
        except ValueError:
            return Response(
                {"detail": "Parâmetros 'year' e 'month' precisam ser inteiros válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = f"dashboard:{firm_id}:{year}:{month}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

        honorarios_agg = ParcelaHonorario.objects.filter(
            honorario__firm_id=firm_id,
            due_date__gte=start_date,
            due_date__lt=end_date,
        ).aggregate(
            recebido=Sum(Case(When(status="RECEBIDO", then="amount"), output_field=DecimalField())),
            pendente=Sum(Case(When(status="PENDENTE", then="amount"), output_field=DecimalField())),
        )

        outras_agg = OutraEntradaInstallment.objects.filter(
            outra_entrada__firm_id=firm_id,
            due_date__gte=start_date,
            due_date__lt=end_date,
        ).aggregate(
            recebido=Sum(Case(When(status="RECEBIDO", then="amount"), output_field=DecimalField())),
            pendente=Sum(Case(When(status="PENDENTE", then="amount"), output_field=DecimalField())),
        )

        entradas_mes = float(honorarios_agg["recebido"] or 0) + float(outras_agg["recebido"] or 0)
        a_receber = float(honorarios_agg["pendente"] or 0) + float(outras_agg["pendente"] or 0)

        saidas_mes = ParcelaDespesa.objects.filter(
            expense__firm_id=firm_id,
            expense__is_active=True,
            due_date__gte=start_date,
            due_date__lt=end_date,
            is_paid=True,
        ).aggregate(total=Sum("amount"))["total"] or 0.0

        saldo_liquido = entradas_mes - float(saidas_mes)

        saldo_em_conta = BankAccount.objects.filter(
            firm_id=firm_id
        ).aggregate(total=Sum("current_balance"))["total"] or 0.0

        trinta = hoje - datetime.timedelta(days=30)
        sessenta = hoje - datetime.timedelta(days=60)
        noventa = hoje - datetime.timedelta(days=90)

        _aging_filter = dict(status="PENDENTE", due_date__lt=hoje)
        _aging_cases = dict(
            total=Sum("amount"),
            ate_30=Sum(Case(When(due_date__gte=trinta, then="amount"), output_field=DecimalField())),
            de_31_60=Sum(Case(When(due_date__gte=sessenta, due_date__lt=trinta, then="amount"), output_field=DecimalField())),
            de_61_90=Sum(Case(When(due_date__gte=noventa, due_date__lt=sessenta, then="amount"), output_field=DecimalField())),
            acima_90=Sum(Case(When(due_date__lt=noventa, then="amount"), output_field=DecimalField())),
        )

        atraso_hon = ParcelaHonorario.objects.filter(
            honorario__firm_id=firm_id, **_aging_filter
        ).aggregate(**_aging_cases)

        atraso_outras = OutraEntradaInstallment.objects.filter(
            outra_entrada__firm_id=firm_id, **_aging_filter
        ).aggregate(**_aging_cases)

        em_atraso = float(atraso_hon["total"] or 0) + float(atraso_outras["total"] or 0)
        aging = {
            "ate_30_dias": float((atraso_hon["ate_30"] or 0) + (atraso_outras["ate_30"] or 0)),
            "de_31_a_60_dias": float((atraso_hon["de_31_60"] or 0) + (atraso_outras["de_31_60"] or 0)),
            "de_61_a_90_dias": float((atraso_hon["de_61_90"] or 0) + (atraso_outras["de_61_90"] or 0)),
            "acima_de_90_dias": float((atraso_hon["acima_90"] or 0) + (atraso_outras["acima_90"] or 0)),
        }

        track_event(
            user=user,
            event_name="dashboard_financeiro_visualizado",
            properties={"ano": year, "mes": month},
        )

        result = {
            "ano_referencia": year,
            "mes_referencia": month,
            "entradas_do_mes": float(entradas_mes),
            "a_receber": float(a_receber),
            "saidas_do_mes": float(saidas_mes),
            "saldo_liquido": float(saldo_liquido),
            "saldo_em_conta": float(saldo_em_conta),
            "em_atraso": em_atraso,
            "aging_inadimplencia": aging,
        }
        cache.set(cache_key, result, timeout=300)
        return Response(result, status=status.HTTP_200_OK)