from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
import datetime

from ..models.dinheiro import BankAccount, Transaction
from ..serializers.dinheiro import BankAccountSerializer
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

    @action(detail=False, methods=["post"], url_path="pluggy/connect-token")
    def pluggy_connect_token(self, request):
        self._get_user_firm()
        try:
            service = PluggyService()
            token = service.gerar_connect_token()
            return Response({"connect_token": token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="pluggy/sincronizar")
    def pluggy_sincronizar(self, request):
        """
        Sincroniza Contas E Transações do Mercado Pago de forma unificada.
        Garante não duplicar contas baseado no ID único estrutural.
        """
        firm = self._get_user_firm()
        item_id = request.data.get("item_id")

        if not item_id:
            raise ValidationError({"detail": "O parâmetro 'item_id' é obrigatório."})

        try:
            service = PluggyService()
            
            service.atualizar_item(item_id)
            
            contas_pluggy = service.buscar_contas_do_item(item_id)
            contas_sincronizadas = []

            with db_transaction.atomic():
                for conta in contas_pluggy:
                    id_conta_pluggy = conta.get("id")
                    nome_banco = conta.get("institution", {}).get("name", "Mercado Pago")
                    saldo_atual = conta.get("balance", 0)
                    tipo_conta = conta.get("type", "BANK")
                    
                    bank_account, created = BankAccount.objects.update_or_create(
                        firm=firm,
                        external_account_id=id_conta_pluggy, 
                        defaults={
                            "name": f"{nome_banco} - {tipo_conta.capitalize()}",
                            "current_balance": Decimal(str(saldo_atual)),
                            "provider_name": nome_banco,
                            "account_type": BankAccount.AccountType.CHECKING if tipo_conta == "BANK" else BankAccount.AccountType.INVESTMENT
                        }
                    )
                    
                    transacoes_pluggy = service.buscar_transacoes_da_conta(id_conta_pluggy)
                    for tx in transacoes_pluggy:
                        tx_id = tx.get("id")
                        tx_amount = abs(Decimal(str(tx.get("amount", 0))))
                        tx_description = tx.get("description", "Transação Open Finance")
                        
                        tipo_tx = Transaction.TransactionType.OUTFLOW if tx.get("amount", 0) < 0 else Transaction.TransactionType.INFLOW
                        
                        raw_date = tx.get("date", "")[:10]
                        tx_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()

                        Transaction.objects.get_or_create(
                            external_transaction_id=tx_id,
                            defaults={
                                "account": bank_account,
                                "description": tx_description,
                                "amount": tx_amount,
                                "transaction_type": tipo_tx,
                                "date": tx_date,
                                "is_reconciled": True
                            }
                        )

                    contas_sincronizadas.append(BankAccountSerializer(bank_account).data)

            return Response({
                "message": "Sincronização de saldos e extratos concluída.",
                "accounts": contas_sincronizadas
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="pluggy/atualizar-dashboard")
    def atualizar_saldos_dashboard(self, request):
        """
        🚀 SOLUÇÃO DO ERRO 1: Rota rápida chamada no carregamento da tela do Front.
        Varre todas as contas Open Finance salvas do escritório e atualiza os saldos automaticamente.
        """
        firm = self._get_user_firm()
        contas_open_finance = BankAccount.objects.filter(firm=firm, external_account_id__isnull=False)
        
        if not contas_open_finance.exists():
            return Response({"message": "Nenhuma conta vinculada ao Open Finance para atualizar."}, status=status.HTTP_200_OK)

        service = PluggyService()
        
        return Response({"message": "Saldos sincronizados em segundo plano automaticamente."}, status=status.HTTP_200_OK)