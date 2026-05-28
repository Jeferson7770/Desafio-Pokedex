# src/expenses/utils/motor_prioridade.py
from decimal import Decimal
from django.db import transaction as db_transaction
import datetime
from ...dinheiro.models.dinheiro import BankAccount
from ...expenses.models.expenses import ParcelaDespesa
from ..models.motor import SimulacaoPrioridade, ItemSimulacaoPrioridade

class MotorPrioridadeEngine:
    PRIORITY_WEIGHTS = {
        "LEGAL": 1,
        "OPERACIONAL": 2,
        "OPCIONAL": 3,
    }

    def __init__(self, firm):
        self.firm = firm

    def obter_saldo_consolidado(self):
        saldos = BankAccount.objects.filter(firm=self.firm).values_list('current_balance', flat=True)
        return sum(saldos) or Decimal("0.00")

    def calcular_e_salvar(self, ano, mes):
        saldo_disponivel = self.obter_saldo_consolidado()
        reference_date = datetime.date(ano, mes, 1)

        parcelas = ParcelaDespesa.objects.filter(
            expense__firm=self.firm,
            is_paid=False,
            due_date__year=ano,
            due_date__month=mes,
            expense__is_active=True
        ).select_related('expense')

        def criterio_ordenacao(p):
            peso_prioridade = self.PRIORITY_WEIGHTS.get(p.expense.priority, 99)
            taxa_mensal = p.expense.interest_rate_month or Decimal("0.00")
            juro_diario = (p.amount * (taxa_mensal / Decimal("100.00"))) / Decimal("30")
            return (peso_prioridade, -juro_diario, p.due_date)

        parcelas_ordenadas = sorted(parcelas, key=criterio_ordenacao)
        saldo_restante = saldo_disponivel

        with db_transaction.atomic():
            SimulacaoPrioridade.objects.filter(firm=self.firm, reference_date=reference_date).delete()

            simulacao = SimulacaoPrioridade.objects.create(
                firm=self.firm,
                reference_date=reference_date,
                saldo_total_disponivel=saldo_disponivel,
                saldo_restante_pos_pagamentos=saldo_disponivel
            )

            for parcela in parcelas_ordenadas:
                if saldo_restante >= parcela.amount:
                    status_rec = ItemSimulacaoPrioridade.StatusRecomendacao.RECOMENDADO
                    saldo_restante -= parcela.amount
                else:
                    status_rec = ItemSimulacaoPrioridade.StatusRecomendacao.NAO_COBERTO

                ItemSimulacaoPrioridade.objects.create(
                    simulacao=simulacao,
                    parcela=parcela,
                    status_recomendacao=status_rec,
                    amount_snapshot=parcela.amount,
                    late_interest_snapshot=parcela.late_interest_cost
                )

            simulacao.saldo_restante_pos_pagamentos = saldo_restante
            simulacao.save()

        return simulacao