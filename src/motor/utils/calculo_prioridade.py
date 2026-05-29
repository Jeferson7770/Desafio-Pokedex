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

    def _obter_parcelas_ordenadas_padrao(self, ano, mes):
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

        return sorted(parcelas, key=criterio_ordenacao)

    def calcular_dinamico(self, ano, mes):
        """Retorna os dados respeitando a ordem gravada no banco (se houver) ou o cálculo padrão."""
        reference_date = datetime.date(ano, mes, 1)
        
        simulacao_salva = SimulacaoPrioridade.objects.filter(
            firm=self.firm, reference_date=reference_date
        ).prefetch_related('items__parcela__expense').first()

        if simulacao_salva:
            recomendados = []
            nao_cobertos = []
            
            for item in simulacao_salva.items.all():
                item_data = {
                    "parcela": item.parcela.id,
                    "expense_title": item.parcela.expense.title,
                    "category": item.parcela.expense.category,
                    "priority": item.parcela.expense.priority,
                    "due_date": item.parcela.due_date.strftime("%Y-%m-%d"),
                    "amount_snapshot": float(item.amount_snapshot),
                    "late_interest_snapshot": float(item.late_interest_snapshot),
                    "status_recomendacao": item.status_recomendacao
                }
                if item.status_recomendacao == "RECOMENDADO":
                    recomendados.append(item_data)
                else:
                    nao_cobertos.append(item_data)

            return {
                "id": simulacao_salva.id,
                "reference_period": f"{ano}-{str(mes).zfill(2)}",
                "saldo_total_disponivel": float(simulacao_salva.saldo_total_disponivel),
                "saldo_restante_pos_pagamentos": float(simulacao_salva.saldo_restante_pos_pagamentos),
                "pagamentos_recomendados": recomendados,
                "pagamentos_nao_cobertos": nao_cobertos
            }

        saldo_disponivel = self.obter_saldo_consolidado()
        parcelas_ordenadas = self._obter_parcelas_ordenadas_padrao(ano, mes)
        saldo_restante = saldo_disponivel

        recomendados = []
        nao_cobertos = []

        for parcela in parcelas_ordenadas:
            item_data = {
                "parcela": parcela.id,
                "expense_title": parcela.expense.title,
                "category": parcela.expense.category,
                "priority": parcela.expense.priority,
                "due_date": parcela.due_date.strftime("%Y-%m-%d"),
                "amount_snapshot": float(parcela.amount),
                "late_interest_snapshot": float(parcela.late_interest_cost)
            }

            if saldo_restante >= parcela.amount:
                item_data["status_recomendacao"] = "RECOMENDADO"
                saldo_restante -= parcela.amount
                recomendados.append(item_data)
            else:
                item_data["status_recomendacao"] = "NAO_COBERTO"
                nao_cobertos.append(item_data)

        return {
            "id": None,
            "reference_period": f"{ano}-{str(mes).zfill(2)}",
            "saldo_total_disponivel": float(saldo_disponivel),
            "saldo_restante_pos_pagamentos": float(saldo_restante),
            "pagamentos_recomendados": recomendados,
            "pagamentos_nao_cobertos": nao_cobertos
        }

    def calcular_e_salvar(self, ano, mes):
        """Calcula e efetivamente grava os dados salvando a ordem sequencial."""
        saldo_disponivel = self.obter_saldo_consolidado()
        reference_date = datetime.date(ano, mes, 1)
        parcelas_ordenadas = self._obter_parcelas_ordenadas_padrao(ano, mes)
        saldo_restante = saldo_disponivel

        with db_transaction.atomic():
            SimulacaoPrioridade.objects.filter(firm=self.firm, reference_date=reference_date).delete()

            simulacao = SimulacaoPrioridade.objects.create(
                firm=self.firm,
                reference_date=reference_date,
                saldo_total_disponivel=saldo_disponivel,
                saldo_restante_pos_pagamentos=saldo_disponivel
            )

            for index, parcela in enumerate(parcelas_ordenadas):
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
                    late_interest_snapshot=parcela.late_interest_cost,
                    ordem=index
                )

            simulacao.saldo_restante_pos_pagamentos = saldo_restante
            simulacao.save()

        return simulacao