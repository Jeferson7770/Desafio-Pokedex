from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
import datetime

from ..models.expenses import Expense, ParcelaDespesa
from ..serializers.expenses import ExpenseSerializer, ExpenseDeferralSerializer


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

        if year and month:
            try:
                queryset = queryset.filter(
                    due_date__year=int(year),
                    due_date__month=int(month)
                )
            except ValueError:
                raise ValidationError("Os parâmetros 'year' e 'month' precisam ser números inteiros válidos.")

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
            raise ValidationError("Parcela não encontrada ou acesso negado.")

        serializer = ExpenseDeferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            installment=installment,
            original_date=installment.due_date
        )

        installment.due_date = serializer.validated_data["new_date"]
        
        if serializer.validated_data.get("penalty_amount"):
            installment.amount += serializer.validated_data["penalty_amount"]
            
        installment.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="yearly-summary")
    def yearly_summary(self, request):
        """
        Retorna em uma única chamada todas as despesas dos últimos 12 meses
        (Ex: Se estamos em Maio/2026, busca de Maio/2025 até hoje), agrupadas por mês.
        """
        today = timezone.localdate()
        
        try:
            start_date = today.replace(year=today.year - 1)
        except ValueError:
            start_date = today - datetime.timedelta(days=365)

        expenses = Expense.objects.filter(
            firm__members__user=request.user,
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
                    "expenses": []
                }
            
            aggregated_data[year_month]["expenses"].append(expense_data)
            aggregated_data[year_month]["total_amount"] += float(expense_data["amount"])

        sorted_summary = sorted(aggregated_data.values(), key=lambda x: x["period"], reverse=True)

        return Response(sorted_summary, status=status.HTTP_200_OK)