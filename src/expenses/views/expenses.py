from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import ExtractYear, ExtractMonth
import datetime

from ..models.expenses import Expense, ParcelaDespesa
from ...fees.models.honorarios import ParcelaHonorario
from ...finance.models.dinheiro import BankAccount
from ..serializers.expenses import ExpenseSerializer, ExpenseDeferralSerializer
from ...users.utils.telemetry import track_event


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuário não possui nenhuma empresa vinculada.")
        return membership.firm

    def get_queryset(self):
        queryset = Expense.objects.filter(
            firm__members__user=self.request.user,
            is_active=True
        ).prefetch_related('installments__deferrals')

        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if year and month:
            try:
                queryset = queryset.filter(
                    due_date__year=int(year),
                    due_date__month=int(month)
                )
            except ValueError:
                track_event(
                    user=self.request.user,
                    event_name="despesas_filtro_erro",
                    properties={"year_tentado": year, "month_tentado": month, "motivo": "valores_nao_inteiros"}
                )
                raise ValidationError("Os parâmetros 'year' e 'month' precisam ser números inteiros válidos.")

        if start_date and end_date:
            queryset = queryset.filter(due_date__range=[start_date, end_date])
        elif start_date or end_date:
            raise ValidationError("Os parâmetros 'start_date' e 'end_date' devem ser enviados juntos.")

        return queryset.order_by("due_date")

    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if year and month:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        track_event(
            user=request.user,
            event_name="despesa_criada_sucesso",
            properties={
                "expense_id": serializer.data.get("id"),
                "amount": float(serializer.data.get("amount", 0)),
                "has_installments": len(serializer.data.get("installments", [])) > 0
            }
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        firm = self._get_user_firm(user)
        serializer.save(firm=firm)

    @action(detail=False, methods=["post"], url_path="defer-installment/(?P<installment_pk>[^/.]+)")
    def defer_installment(self, request, installment_pk=None):
        try:
            installment = ParcelaDespesa.objects.get(
                pk=installment_pk, 
                expense__firm__members__user=request.user
            )
        except ParcelaDespesa.DoesNotExist:
            track_event(
                user=request.user,
                event_name="despesa_adiamento_falha",
                properties={"installment_pk": installment_pk, "motivo_erro": "parcela_nao_encontrada"}
            )
            raise ValidationError("Parcela não encontrada ou acesso negado.")

        serializer = ExpenseDeferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        original_date = installment.due_date
        new_date = serializer.validated_data["new_date"]
        penalty_amount = serializer.validated_data.get("penalty_amount", 0)

        serializer.save(
            installment=installment,
            original_date=original_date
        )

        installment.due_date = new_date
        
        if penalty_amount:
            installment.amount += penalty_amount
            
        installment.save()

        track_event(
            user=request.user,
            event_name="despesa_parcela_adiada",
            properties={
                "installment_id": installment.id,
                "expense_id": installment.expense.id,
                "original_due_date": str(original_date),
                "new_due_date": str(new_date),
                "penalty_amount": float(penalty_amount) if penalty_amount else 0.0
            }
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="yearly-summary")
    def yearly_summary(self, request):
        firm = self._get_user_firm(request.user)
        today = timezone.localdate()
        
        try:
            start_date = today.replace(year=today.year - 1)
        except ValueError:
            start_date = today - datetime.timedelta(days=365)

        expenses = Expense.objects.filter(
            firm=firm,
            is_active=True,
            due_date__range=[start_date, today]
        ).prefetch_related('installments__deferrals').order_by("due_date")

        serializer = self.get_serializer(expenses, many=True)

        aggregated_data = {}
        for expense_data in serializer.data:
            due_date_str = expense_data["due_date"]
            year_month = due_date_str[:7] 

            if year_month not in aggregated_data:
                aggregated_data[year_month] = {
                    "period": year_month,
                    "total_amount": 0.0,
                    "expenses": [],
                    "dashboard": {
                        "entradas_do_mes": 0.0,
                        "a_receber": 0.0,
                        "saidas_do_mes": 0.0,
                        "saldo_liquido": 0.0
                    }
                }
            
            aggregated_data[year_month]["expenses"].append(expense_data)
            aggregated_data[year_month]["total_amount"] += float(expense_data["amount"])

        honorarios_bulk = ParcelaHonorario.objects.filter(
            honorario__firm=firm,
            due_date__range=[start_date, today]
        ).annotate(
            ano=ExtractYear('due_date'),
            mes=ExtractMonth('due_date')
        ).values('ano', 'mes', 'status').annotate(
            total=Sum('amount')
        )

        despesas_bulk = ParcelaDespesa.objects.filter(
            expense__firm=firm,
            expense__is_active=True,
            due_date__range=[start_date, today]
        ).annotate(
            ano=ExtractYear('due_date'),
            mes=ExtractMonth('due_date')
        ).values('ano', 'mes', 'is_paid').annotate(
            total=Sum('amount')
        )

        for item in honorarios_bulk:
            key = f"{item['ano']}-{str(item['mes']).zfill(2)}"
            if key in aggregated_data:
                total_val = float(item['total'] or 0.0)
                if item['status'] == "RECEBIDO":
                    aggregated_data[key]["dashboard"]["entradas_do_mes"] = total_val
                elif item['status'] == "PENDENTE":
                    aggregated_data[key]["dashboard"]["a_receber"] = total_val

        for item in despesas_bulk:
            key = f"{item['ano']}-{str(item['mes']).zfill(2)}"
            if key in aggregated_data:
                total_val = float(item['total'] or 0.0)
                if not item['is_paid']:
                    aggregated_data[key]["dashboard"]["saidas_do_mes"] = total_val

        for period, period_data in aggregated_data.items():
            dash = period_data["dashboard"]
            dash["saldo_liquido"] = dash["entradas_do_mes"] - dash["saidas_do_mes"]

        saldo_em_conta = BankAccount.objects.filter(firm=firm).aggregate(total=Sum("current_balance"))["total"] or 0.0

        sorted_summary = sorted(aggregated_data.values(), key=lambda x: x["period"], reverse=True)

        response_payload = {
            "summary": sorted_summary,
            "total_bank_balance": float(saldo_em_conta)
        }

        track_event(
            user=request.user,
            event_name="visualizou_resumo_despesas_anual",
            properties={
                "meses_com_dados_count": len(sorted_summary),
                "total_bank_balance": float(saldo_em_conta)
            }
        )

        return Response(response_payload, status=status.HTTP_200_OK)