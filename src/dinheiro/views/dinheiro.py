from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from django.db import transaction as db_transaction

from ..models.dinheiro import BankAccount, Transaction
from ..serializers.dinheiro import BankAccountSerializer, TransactionSerializer

class BankAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(firm__members__user=self.request.user)

    def perform_create(self, serializer):
        membership = self.request.user.firm_memberships.first()
        if not membership:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "O usuário precisa estar vinculado a um escritório para criar uma conta bancária."})
        
        initial_balance = serializer.validated_data.get("initial_balance", 0)
        serializer.save(firm=membership.firm, current_balance=initial_balance)


class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(account__firm__members__user=self.request.user)

    def perform_create(self, serializer):
        with db_transaction.atomic():
            instance = serializer.save()
            account = instance.account
            
            if instance.transaction_type == Transaction.TransactionType.INFLOW:
                account.current_balance += instance.amount
            else:
                account.current_balance -= instance.amount
            account.save()

    def perform_destroy(self, instance):
        with db_transaction.atomic():
            account = instance.account
            
            if instance.transaction_type == Transaction.TransactionType.INFLOW:
                account.current_balance -= instance.amount
            else:
                account.current_balance += instance.amount
            account.save()
            
            instance.delete()

    @action(detail=False, methods=["get"], url_path="cash-flow-summary")
    def cash_flow_summary(self, request):
        """Retorna o total consolidado de entradas, saídas e o saldo líquido"""
        queryset = self.get_queryset()
        
        inflows = queryset.filter(transaction_type=Transaction.TransactionType.INFLOW).aggregate(total=Sum('amount'))['total'] or 0
        outflows = queryset.filter(transaction_type=Transaction.TransactionType.OUTFLOW).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            "total_inflows": float(inflows),
            "total_outflows": float(outflows),
            "net_cash_flow": float(inflows - outflows)
        }, status=status.HTTP_200_OK)