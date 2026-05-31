from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal

from ..models.dinheiro import BankAccount, Transaction
from ..serializers.dinheiro import BankAccountSerializer, TransactionSerializer
from ..services.pluggy import PluggyService  

class BankAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(firm__members__user=self.request.user)

    def _get_user_firm(self):
        membership = self.request.user.firm_memberships.first()
        if not membership:
            raise ValidationError({"detail": "O usuário precisa estar vinculado a um escritório para esta operação."})
        return membership.firm

    def perform_create(self, serializer):
        firm = self._get_user_firm()
        initial_balance = serializer.validated_data.get("initial_balance", 0)
        serializer.save(firm=firm, current_balance=initial_balance)

    @action(detail=False, methods=["post"], url_path="pluggy/connect-token")
    def pluggy_connect_token(self, request):
        """
        POST /api/dinheiro/bank-accounts/pluggy/connect-token/
        Gera o token temporário para o Frontend abrir o Widget da Pluggy com segurança.
        """
        self._get_user_firm()
        
        try:
            service = PluggyService()
            token = service.gerar_connect_token()
            return Response({"connect_token": token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar connect token na Pluggy: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="pluggy/sincronizar")
    def pluggy_sincronizar(self, request):
        """
        POST /api/dinheiro/bank-accounts/pluggy/sincronizar/
        Recebe o 'item_id' do frontend, busca as contas conectadas na Pluggy
        e atualiza/cria os registros na tabela BankAccount usando as colunas corretas.
        """
        firm = self._get_user_firm()
        item_id = request.data.get("item_id")

        if not item_id:
            raise ValidationError({"detail": "O parâmetro 'item_id' é obrigatório para sincronizar as contas."})

        try:
            service = PluggyService()
            contas_pluggy = service.buscar_contas_do_item(item_id)
            
            contas_sincronizadas = []

            with db_transaction.atomic():
                for conta in contas_pluggy:
                    id_conta_pluggy = conta.get("id")
                    nome_banco = conta.get("institution", {}).get("name", "Banco Conectado")
                    saldo_atual = conta.get("balance", 0)
                    tipo_conta = conta.get("type", "BANK")
                    
                    bank_account, created = BankAccount.objects.update_or_create(
                        firm=firm,
                        external_account_id=id_conta_pluggy,
                        defaults={
                            "name": f"{nome_banco} - {tipo_conta.capitalize()}",
                            "current_balance": Decimal(str(saldo_atual)),
                            "provider_name": "PLUGGY",
                        }
                    )
                    
                    contas_sincronizadas.append(BankAccountSerializer(bank_account).data)

            return Response({
                "message": f"Sincronização concluída com sucesso. {len(contas_sincronizadas)} conta(s) afetada(s).",
                "accounts": contas_sincronizadas
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Erro na sincronização de dados com a Pluggy: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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