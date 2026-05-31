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
import calendar
import threading
import re

from ..models.dinheiro import BankAccount, Transaction
from ...honorarios.models.honorarios import Honorario
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

    def _processar_extrato_background(self, contas_para_extrato, primeiro_dia_mes, ultimo_dia_do_mes, ano_atual, mes_atual):
        service = PluggyService()
        for bank_account, id_conta_pluggy in contas_para_extrato:
            try:
                transacoes_pluggy = service.buscar_transacoes_da_conta(
                    id_conta_pluggy, 
                    from_date=primeiro_dia_mes, 
                    to_date=ultimo_dia_do_mes
                )
                
                for tx in transacoes_pluggy:
                    raw_date = tx.get("date", "")[:10]
                    tx_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()

                    if tx_date.year != ano_atual or tx_date.month != mes_atual:
                        continue

                    tx_id = tx.get("id")
                    tx_amount = abs(Decimal(str(tx.get("amount", 0))))
                    tx_description = tx.get("description", "Transação Open Finance")
                    tipo_tx = Transaction.TransactionType.OUTFLOW if tx.get("amount", 0) < 0 else Transaction.TransactionType.INFLOW
                    
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
            except Exception as tx_err:
                print(f"Erro background item {id_conta_pluggy}: {str(tx_err)}")

    @action(detail=False, methods=["post"], url_path="pluggy/sincronizar")
    def pluggy_sincronizar(self, request):
        firm = self._get_user_firm()
        item_id = request.data.get("item_id")

        if not item_id:
            raise ValidationError({"detail": "O parâmetro 'item_id' é obrigatório."})

        try:
            service = PluggyService()
            
            try:
                service.atualizar_item(item_id)
            except Exception as update_err:
                print(f"Aviso atualização item {item_id}: {str(update_err)}")
            
            contas_pluggy = service.buscar_contas_do_item(item_id)
            contas_sincronizadas = []
            contas_para_extrato = []

            with db_transaction.atomic():
                for conta in contas_pluggy:
                    id_conta_pluggy = conta.get("id")
                    
                    nome_da_conta_pluggy = conta.get("name") or ""
                    
                    nome_original_pluggy = (
                        conta.get("institution", {}).get("name") if conta.get("institution") else None
                    ) or conta.get("providerName") or "Banco Conectado"
                    
                    if "Banco Conectado" not in nome_original_pluggy and nome_original_pluggy != "Banco Conectado":
                        nome_com_prefixo = f"Banco Conectado - {nome_original_pluggy}"
                    else:
                        nome_com_prefixo = nome_original_pluggy

                    nome_instituicao = re.sub(r"^Banco Conectado\s*(-\s*)?", "", nome_com_prefixo).strip()
                    if not nome_instituicao:
                        nome_instituicao = "Banco Conectado"

                    if nome_da_conta_pluggy:
                        nome_exibicao = f"{nome_instituicao} - {nome_da_conta_pluggy}"
                    else:
                        nome_exibicao = nome_instituicao

                    saldo_atual = conta.get("balance")
                    if saldo_atual is None:
                        saldo_atual = conta.get("availableBalance", 0)
                    
                    tipo_conta = conta.get("type", "BANK")
                    
                    bank_account, created = BankAccount.objects.update_or_create(
                        firm=firm,
                        external_account_id=id_conta_pluggy, 
                        defaults={
                            "name": nome_exibicao,
                            "current_balance": Decimal(str(saldo_atual)),
                            "provider_name": nome_instituicao,
                            "account_type": BankAccount.AccountType.CHECKING if tipo_conta in ["BANK", "WALLET"] else BankAccount.AccountType.INVESTMENT
                        }
                    )
                    contas_sincronizadas.append(bank_account)
                    contas_para_extrato.append((bank_account, id_conta_pluggy))

            hoje = datetime.date.today()
            primeiro_dia_mes = hoje.replace(day=1).strftime("%Y-%m-%d")
            ultimo_dia_do_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1]).strftime("%Y-%m-%d")

            threading.Thread(
                target=self._processar_extrato_background,
                args=(contas_para_extrato, primeiro_dia_mes, ultimo_dia_do_mes, hoje.year, hoje.month),
                daemon=True
            ).start()

            serializer = BankAccountSerializer(contas_sincronizadas, many=True)
            return Response({
                "message": "Os dados das contas foram carregados. As transações estão sendo sincronizadas em segundo plano e aparecerão em breve.",
                "accounts": serializer.data
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="pluggy/connect-token")
    def pluggy_connect_token(self, request):
        self._get_user_firm()
        try:
            service = PluggyService()
            token = service.gerar_connect_token()
            return Response({"connect_token": token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="pluggy/atualizar-dashboard")
    def atualizar_saldos_dashboard(self, request):
        firm = self._get_user_firm()
        contas_open_finance = BankAccount.objects.filter(firm=firm, external_account_id__isnull=False)
        if not contas_open_finance.exists():
            return Response({"message": "Nenhuma conta vinculada ao Open Finance para atualizar."}, status=status.HTTP_200_OK)
        return Response({"message": "Saldos sincronizados em segundo plano automaticamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="pluggy/saldo-bancario-total")
    def saldo_bancario_total(self, request):
        firm = self._get_user_firm()
        saldo_total = BankAccount.objects.filter(firm=firm).aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
        return Response({
            "total_bank_balance": float(saldo_total)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="pluggy/disponibilidade-financeira")
    def disponibilidade_financeira(self, request):
        firm = self._get_user_firm()
        hoje = datetime.date.today()
        
        saldo_bancario = BankAccount.objects.filter(firm=firm).aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
        
        honorarios_recebidos_mes = Honorario.objects.filter(
            firm=firm,
            status=Honorario.Status.RECEBIDO,
            date__year=hoje.year,
            date__month=hoje.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_disponivel = saldo_bancario + honorarios_recebidos_mes
        
        return Response({
            "total_bank_balance": float(saldo_bancario),
            "received_fees_current_month": float(honorarios_recebidos_mes),
            "total_financial_availability": float(total_disponivel)
        }, status=status.HTTP_200_OK)

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
        queryset = self.get_queryset()
        
        inflows = queryset.filter(transaction_type=Transaction.TransactionType.INFLOW).aggregate(total=Sum('amount'))['total'] or 0
        outflows = queryset.filter(transaction_type=Transaction.TransactionType.OUTFLOW).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            "total_inflows": float(inflows),
            "total_outflows": float(outflows),
            "net_cash_flow": float(inflows - outflows)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="top-cinco-transacoes")
    def top_cinco_transacoes_mes(self, request):
        hoje = datetime.date.today()
        
        queryset = self.get_queryset().filter(
            date__year=hoje.year,
            date__month=hoje.month
        ).order_by("-amount")[:5]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)