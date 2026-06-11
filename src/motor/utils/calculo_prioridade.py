from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Prefetch, Sum
import datetime
from ...finance.models.dinheiro import BankAccount
from ...expenses.models.expenses import ParcelaDespesa
from ..models.motor import SimulacaoPrioridade, ItemSimulacaoPrioridade


class MotorPrioridadeEngine:
    PRIORITY_WEIGHTS = {
        "LEGAL": 1,
        "CRITICO": 1,
        "LEGAL / CRÍTICO": 1,
        "OPERACIONAL": 2,
        "OPCIONAL": 3,
    }

    def __init__(self, firm):
        self.firm = firm

    def obter_saldo_consolidado(self):
        result = BankAccount.objects.filter(firm=self.firm).aggregate(total=Sum("current_balance"))
        return result["total"] or Decimal("0.00")

    def _obter_parcelas_ordenadas_padrao(self, ano, mes):
        parcelas = ParcelaDespesa.objects.filter(
            expense__firm=self.firm,
            is_paid=False,
            due_date__year=ano,
            due_date__month=mes,
            expense__is_active=True
        ).select_related("expense")

        def criterio_ordenacao(p):
            prioridade_crua = str(p.expense.priority).strip().upper()

            if "LEGAL" in prioridade_crua or "CRÍTICO" in prioridade_crua or "CRITICO" in prioridade_crua:
                peso_prioridade = 1
            elif "OPERACIONAL" in prioridade_crua:
                peso_prioridade = 2
            else:
                peso_prioridade = 3

            taxa_mensal = p.expense.interest_rate_month or Decimal("0.00")
            juro_diario = (p.amount * (taxa_mensal / Decimal("100.00"))) / Decimal("30")

            return (peso_prioridade, -juro_diario, p.due_date)

        return sorted(parcelas, key=criterio_ordenacao)

    def calcular_dinamico(self, ano, mes):
        reference_date = datetime.date(ano, mes, 1)

        # Prefetch with ordering baked in so the cache is used (avoid re-query with .order_by())
        items_qs = (
            ItemSimulacaoPrioridade.objects
            .order_by("ordem")
            .select_related("parcela__expense")
        )
        simulacao_salva = (
            SimulacaoPrioridade.objects
            .filter(firm=self.firm, reference_date=reference_date)
            .prefetch_related(Prefetch("items", queryset=items_qs))
            .first()
        )

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
                    "status_recomendacao": item.status_recomendacao,
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
                "pagamentos_nao_cobertos": nao_cobertos,
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
                "late_interest_snapshot": float(parcela.late_interest_cost),
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
            "pagamentos_nao_cobertos": nao_cobertos,
        }

    def salvar_configuracao_da_tela(self, ano, mes, itens_da_tela):
        saldo_disponivel = self.obter_saldo_consolidado()
        reference_date = datetime.date(ano, mes, 1)
        saldo_restante = saldo_disponivel

        # Pre-fetch ALL parcelas in one query instead of one per loop iteration
        parcela_ids = [item.get("parcela") for item in itens_da_tela if item.get("parcela")]
        parcelas_map = {
            p.id: p
            for p in ParcelaDespesa.objects.filter(
                id__in=parcela_ids,
                expense__firm=self.firm
            ).select_related("expense")
        }

        with db_transaction.atomic():
            SimulacaoPrioridade.objects.filter(firm=self.firm, reference_date=reference_date).delete()

            simulacao = SimulacaoPrioridade.objects.create(
                firm=self.firm,
                reference_date=reference_date,
                saldo_total_disponivel=saldo_disponivel,
                saldo_restante_pos_pagamentos=saldo_disponivel,
            )

            items_to_create = []
            for index, item_front in enumerate(itens_da_tela):
                parcela = parcelas_map.get(item_front.get("parcela"))
                if not parcela:
                    continue

                status_rec = item_front.get("status_recomendacao", "RECOMENDADO")
                if status_rec == "RECOMENDADO" and saldo_restante >= parcela.amount:
                    saldo_restante -= parcela.amount
                else:
                    status_rec = "NAO_COBERTO"

                items_to_create.append(ItemSimulacaoPrioridade(
                    simulacao=simulacao,
                    parcela=parcela,
                    status_recomendacao=status_rec,
                    amount_snapshot=parcela.amount,
                    late_interest_snapshot=parcela.late_interest_cost,
                    ordem=index,
                ))

            ItemSimulacaoPrioridade.objects.bulk_create(items_to_create)

            simulacao.saldo_restante_pos_pagamentos = saldo_restante
            simulacao.save(update_fields=["saldo_restante_pos_pagamentos"])

        return simulacao
