from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models.expenses import Expense, ParcelaDespesa
from ..serializers.expenses import ExpenseSerializer, ExpenseDeferralSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_firm(self, user):
        membership = user.firm_memberships.first()
        if not membership:
            raise ValidationError("User has no firm")
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
        """
        Rota inteligente para adiar uma parcela específica enviando nova data e multa no payload.
        """
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