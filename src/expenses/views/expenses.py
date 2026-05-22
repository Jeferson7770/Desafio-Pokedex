from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from src.expenses.models.expenses import Expense
from src.expenses.models.expenses_deferral import ExpenseDeferral
from src.expenses.serializers.expenses import ExpenseSerializer, ExpenseDeferralSerializer


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
        )

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
        """
        Sobrescreve o list para remover a paginação caso seja uma consulta da Dashboard.
        Isso garante que retorne o array direto [ ... ] pedido pelo front.
        """
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if year and month:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        firm = self._get_user_firm(user)
        serializer.save(firm=firm)

    @action(detail=True, methods=["post"])
    def defer(self, request, pk=None):
        expense = self.get_object()

        serializer = ExpenseDeferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            expense=expense,
            original_date=expense.due_date
        )

        expense.due_date = serializer.validated_data["new_date"]
        expense.save()

        return Response(serializer.data)