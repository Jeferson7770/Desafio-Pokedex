from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Prefetch, Sum
import datetime
from ...finance.models.dinheiro import BankAccount
from ...expenses.models.expenses import ParcelaDespesa
from ...other_income.models.outras_entradas import OutraEntradaInstallment
from ..models.motor import SimulacaoPrioridade, ItemSimulacaoPrioridade


class MotorPrioridadeEngine:
    PRIORITY_WEIGHTS = {
        "CRITICA": 1, "ESPECIAL": 2, "ALTA": 3, "MEDIA_ALTA": 4,
        "MEDIA": 5, "MEDIA_BAIXA": 6, "BAIXA": 7, "INDEFINIDA": 99,
        "LEGAL": 1, "OPERACIONAL": 5, "OPCIONAL": 7,
    }
    CATEGORY_ORDER = {
        "PESSOAL_E_REMUNERACAO": 1, "FISCAL_E_OBRIGACOES_LEGAIS": 2,
        "CUSTAS_PROCESSUAIS_E_JUDICIAIS": 3, "ESTRUTURA_E_OPERACAO": 4,
        "TECNOLOGIA_E_ASSINATURA": 5, "FINANCEIRA": 6,
        "MARKETING_E_AQUISICAO": 7, "MOBILIDADE_E_DESLOCAMENTO": 8,
        "INVESTIMENTOS_NO_ESCRITORIO": 9, "CAPACITACAO_E_DESENVOLVIMENTO": 10,
        "A_CLASSIFICAR": 99,
    }
    PRIORITY_LABELS = {
        "CRITICA": "Crítica", "ESPECIAL": "Especial", "ALTA": "Alta",
        "MEDIA_ALTA": "Média-Alta", "MEDIA": "Média", "MEDIA_BAIXA": "Média-Baixa",
        "BAIXA": "Baixa", "INDEFINIDA": "Indefinida",
    }
    CATEGORY_DEFAULT_PRIORITY = {
        "PESSOAL_E_REMUNERACAO": "CRITICA", "FISCAL_E_OBRIGACOES_LEGAIS": "CRITICA",
        "CUSTAS_PROCESSUAIS_E_JUDICIAIS": "ESPECIAL", "ESTRUTURA_E_OPERACAO": "ALTA",
        "TECNOLOGIA_E_ASSINATURA": "MEDIA_ALTA", "FINANCEIRA": "MEDIA",
        "MARKETING_E_AQUISICAO": "MEDIA", "MOBILIDADE_E_DESLOCAMENTO": "MEDIA_BAIXA",
        "INVESTIMENTOS_NO_ESCRITORIO": "BAIXA", "CAPACITACAO_E_DESENVOLVIMENTO": "BAIXA",
        "A_CLASSIFICAR": "INDEFINIDA",
    }

    def __init__(self, firm):
        self.firm = firm

    def obter_saldo_consolidado(self):
        result = BankAccount.objects.filter(firm=self.firm).aggregate(total=Sum("current_balance"))
        return result["total"] or Decimal("0.00")

    def _sort_key(self, p):
        priority = str(p.expense.priority).strip().upper()
        category = str(p.expense.category).strip().upper()
        taxa = p.expense.interest_rate_month or Decimal("0.00")
        juro_diario = (p.amount * (taxa / Decimal("100.00"))) / Decimal("30")
        return (
            self.PRIORITY_WEIGHTS.get(priority, 50),
            self.CATEGORY_ORDER.get(category, 50),
            -juro_diario,
            p.due_date,
        )

    def _aplicar(self, amount, saldo):
        """Deduz o valor do saldo e retorna (status, novo_saldo). Saldo pode ficar negativo."""
        return ("RECOMENDADO" if saldo >= amount else "NAO_COBERTO"), saldo - amount

    def _item_parcela(self, parcela, status=None, saldo_pos=None, amount=None, interest=None):
        priority = parcela.expense.priority
        item = {
            "tipo": "despesa",
            "parcela": parcela.id,
            "outra_entrada_installment_id": None,
            "expense_title": parcela.expense.title,
            "category": parcela.expense.category,
            "priority": priority,
            "priority_label": self.PRIORITY_LABELS.get(priority, priority),
            "due_date": parcela.due_date.strftime("%Y-%m-%d"),
            "amount_snapshot": float(amount if amount is not None else parcela.amount),
            "late_interest_snapshot": float(interest if interest is not None else parcela.late_interest_cost),
        }
        if status is not None:
            item["status_recomendacao"] = status
            item["saldo_pos_pagamento"] = float(saldo_pos)
        return item

    def _item_outra_entrada(self, inst, status, saldo_pos):
        return {
            "tipo": "outra_entrada",
            "parcela": None,
            "outra_entrada_installment_id": inst.id,
            "expense_title": inst.outra_entrada.title,
            "category": "OUTRAS_ENTRADAS",
            "priority": "MEDIA",
            "priority_label": "Média",
            "due_date": inst.due_date.strftime("%Y-%m-%d"),
            "amount_snapshot": float(inst.amount),
            "late_interest_snapshot": float(inst.late_interest_cost),
            "status_recomendacao": status,
            "saldo_pos_pagamento": float(saldo_pos),
        }

    def _obter_parcelas_periodo(self, ano, mes, exclude_ids=None):
        start = datetime.date(ano, mes, 1)
        end = datetime.date(ano, mes + 1, 1) if mes < 12 else datetime.date(ano + 1, 1, 1)
        qs = ParcelaDespesa.objects.filter(
            expense__firm=self.firm, is_paid=False,
            due_date__gte=start, due_date__lt=end, expense__is_active=True,
        ).select_related("expense")
        if exclude_ids:
            qs = qs.exclude(id__in=exclude_ids)
        parcelas = list(qs)
        rankeaveis = sorted(
            [p for p in parcelas
             if str(p.expense.priority).upper() not in ("INDEFINIDA", "")
             and str(p.expense.category).upper() != "A_CLASSIFICAR"],
            key=self._sort_key,
        )
        pendentes = [
            p for p in parcelas
            if str(p.expense.priority).upper() in ("INDEFINIDA", "")
            or str(p.expense.category).upper() == "A_CLASSIFICAR"
        ]
        return rankeaveis, pendentes

    def _obter_outras_entradas_pendentes(self, start, end):
        return list(
            OutraEntradaInstallment.objects.filter(
                outra_entrada__firm=self.firm,
                status=OutraEntradaInstallment.Status.PENDENTE,
                due_date__gte=start, due_date__lt=end,
            ).select_related("outra_entrada")
        )

    def calcular_dinamico(self, ano, mes):
        start = datetime.date(ano, mes, 1)
        end = datetime.date(ano, mes + 1, 1) if mes < 12 else datetime.date(ano + 1, 1, 1)

        items_qs = ItemSimulacaoPrioridade.objects.order_by("ordem").select_related("parcela__expense")
        simulacao_salva = (
            SimulacaoPrioridade.objects
            .filter(firm=self.firm, reference_date=start)
            .prefetch_related(Prefetch("items", queryset=items_qs))
            .first()
        )

        saldo_disponivel = self.obter_saldo_consolidado()
        saldo = saldo_disponivel
        recomendados, nao_cobertos = [], []

        if simulacao_salva:
            # Processar na ordem exata definida pelo usuario
            parcelas_na_simulacao = set()
            for item in simulacao_salva.items.all():
                parcelas_na_simulacao.add(item.parcela_id)
                status, saldo = self._aplicar(item.amount_snapshot, saldo)
                entry = self._item_parcela(
                    item.parcela, status, saldo,
                    amount=item.amount_snapshot, interest=item.late_interest_snapshot,
                )
                (recomendados if status == "RECOMENDADO" else nao_cobertos).append(entry)
            # Parcelas criadas depois que a simulacao foi salva: appenda por prioridade
            rankeaveis, pendentes_list = self._obter_parcelas_periodo(ano, mes, exclude_ids=parcelas_na_simulacao)
        else:
            rankeaveis, pendentes_list = self._obter_parcelas_periodo(ano, mes)

        for parcela in rankeaveis:
            status, saldo = self._aplicar(parcela.amount, saldo)
            (recomendados if status == "RECOMENDADO" else nao_cobertos).append(
                self._item_parcela(parcela, status, saldo)
            )

        for inst in sorted(self._obter_outras_entradas_pendentes(start, end), key=lambda i: i.due_date):
            status, saldo = self._aplicar(inst.amount, saldo)
            (recomendados if status == "RECOMENDADO" else nao_cobertos).append(
                self._item_outra_entrada(inst, status, saldo)
            )

        return {
            "id": simulacao_salva.id if simulacao_salva else None,
            "reference_period": f"{ano}-{str(mes).zfill(2)}",
            "saldo_total_disponivel": float(saldo_disponivel),
            "saldo_restante_pos_pagamentos": float(saldo),
            "pagamentos_recomendados": recomendados,
            "pagamentos_nao_cobertos": nao_cobertos,
            "pendentes_categorizacao": [self._item_parcela(p) for p in pendentes_list],
        }

    def salvar_configuracao_da_tela(self, ano, mes, itens_da_tela):
        saldo_disponivel = self.obter_saldo_consolidado()
        reference_date = datetime.date(ano, mes, 1)
        saldo = saldo_disponivel

        parcela_ids = [item.get("parcela") for item in itens_da_tela if item.get("parcela")]
        parcelas_map = {
            p.id: p
            for p in ParcelaDespesa.objects.filter(
                id__in=parcela_ids, expense__firm=self.firm
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
                status, saldo = self._aplicar(parcela.amount, saldo)
                items_to_create.append(ItemSimulacaoPrioridade(
                    simulacao=simulacao,
                    parcela=parcela,
                    status_recomendacao=status,
                    amount_snapshot=parcela.amount,
                    late_interest_snapshot=parcela.late_interest_cost,
                    ordem=index,
                ))

            ItemSimulacaoPrioridade.objects.bulk_create(items_to_create)
            simulacao.saldo_restante_pos_pagamentos = saldo
            simulacao.save(update_fields=["saldo_restante_pos_pagamentos"])

        return simulacao
