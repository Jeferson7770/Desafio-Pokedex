import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Case, When, DecimalField, IntegerField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.cache import cache

from ...fees.models.honorarios import ParcelaHonorario
from ...expenses.models.expenses import ParcelaDespesa
from ...other_income.models.outras_entradas import OutraEntradaInstallment
from ...users.utils.firm_mixin import FirmMixin

LABELS_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _add_months(year, month, delta):
    m = month + delta
    y = year
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


class DashboardView(FirmMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        firm_id = self._get_firm_id()
        if not firm_id:
            return Response(
                {"detail": "Usuário não vinculado a nenhuma empresa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hoje = timezone.localdate()
        try:
            year = int(request.query_params.get("year", hoje.year))
            month = int(request.query_params.get("month", hoje.month))
        except ValueError:
            return Response(
                {"detail": "Parâmetros 'year' e 'month' precisam ser inteiros válidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"dashboard_v2:{firm_id}:{year}:{month}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(*_add_months(year, month, 1), 1)

        result = {
            "periodo": f"{year}-{month:02d}",
            "kpis": self._build_kpis(firm_id, start_date, end_date),
            "fluxo_mensal": self._build_fluxo_mensal(firm_id, year, month, end_date),
            "aging_honorarios": self._build_aging_honorarios(firm_id, hoje),
            "aging_inadimplencia": self._build_aging_inadimplencia(firm_id, hoje),
        }
        cache.set(cache_key, result, timeout=300)
        return Response(result, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------ #

    def _build_kpis(self, firm_id, start_date, end_date):
        hon_mes = ParcelaHonorario.objects.filter(
            honorario__firm_id=firm_id,
            due_date__gte=start_date,
            due_date__lt=end_date,
        ).aggregate(
            recebido=Sum(Case(When(status="RECEBIDO", then="amount"), output_field=DecimalField())),
        )
        outras_mes = OutraEntradaInstallment.objects.filter(
            outra_entrada__firm_id=firm_id,
            due_date__gte=start_date,
            due_date__lt=end_date,
        ).aggregate(
            recebido=Sum(Case(When(status="RECEBIDO", then="amount"), output_field=DecimalField())),
        )
        entradas_do_mes = float(hon_mes["recebido"] or 0) + float(outras_mes["recebido"] or 0)

        # a_receber = TODOS os pendentes, sem filtro de período
        a_receber = float(
            ParcelaHonorario.objects.filter(honorario__firm_id=firm_id, status="PENDENTE")
            .aggregate(t=Sum("amount"))["t"] or 0
        ) + float(
            OutraEntradaInstallment.objects.filter(outra_entrada__firm_id=firm_id, status="PENDENTE")
            .aggregate(t=Sum("amount"))["t"] or 0
        )

        desp_mes = ParcelaDespesa.objects.filter(
            expense__firm_id=firm_id,
            expense__is_active=True,
            due_date__gte=start_date,
            due_date__lt=end_date,
        ).aggregate(
            pagas=Sum(Case(When(is_paid=True, then="amount"), output_field=DecimalField())),
            pendentes=Sum(Case(When(is_paid=False, then="amount"), output_field=DecimalField())),
        )
        saidas_do_mes = float(desp_mes["pagas"] or 0)
        saidas_pendentes = float(desp_mes["pendentes"] or 0)

        return {
            "entradas_do_mes": entradas_do_mes,
            "a_receber": a_receber,
            "saidas_do_mes": saidas_do_mes,
            "saidas_pendentes": saidas_pendentes,
            "saldo_liquido": entradas_do_mes - saidas_do_mes,
        }

    def _build_fluxo_mensal(self, firm_id, year, month, end_date):
        y6, m6 = _add_months(year, month, -5)
        six_start = datetime.date(y6, m6, 1)

        hon_rows = (
            ParcelaHonorario.objects.filter(
                honorario__firm_id=firm_id,
                status="RECEBIDO",
                due_date__gte=six_start,
                due_date__lt=end_date,
            )
            .annotate(mes=TruncMonth("due_date"))
            .values("mes")
            .annotate(total=Sum("amount"))
        )
        outras_rows = (
            OutraEntradaInstallment.objects.filter(
                outra_entrada__firm_id=firm_id,
                status="RECEBIDO",
                due_date__gte=six_start,
                due_date__lt=end_date,
            )
            .annotate(mes=TruncMonth("due_date"))
            .values("mes")
            .annotate(total=Sum("amount"))
        )
        desp_rows = (
            ParcelaDespesa.objects.filter(
                expense__firm_id=firm_id,
                expense__is_active=True,
                due_date__gte=six_start,
                due_date__lt=end_date,
            )
            .annotate(mes=TruncMonth("due_date"))
            .values("mes")
            .annotate(total=Sum("amount"))
        )

        entradas_map: dict[str, float] = {}
        for row in hon_rows:
            k = row["mes"].strftime("%Y-%m")
            entradas_map[k] = entradas_map.get(k, 0.0) + float(row["total"] or 0)
        for row in outras_rows:
            k = row["mes"].strftime("%Y-%m")
            entradas_map[k] = entradas_map.get(k, 0.0) + float(row["total"] or 0)

        saidas_map: dict[str, float] = {
            row["mes"].strftime("%Y-%m"): float(row["total"] or 0) for row in desp_rows
        }

        fluxo = []
        for i in range(6):
            yi, mi = _add_months(year, month, -5 + i)
            k = f"{yi}-{mi:02d}"
            fluxo.append({
                "periodo": k,
                "label": LABELS_PT[mi - 1],
                "entradas": entradas_map.get(k, 0.0),
                "saidas": saidas_map.get(k, 0.0),
            })
        return fluxo

    def _build_aging_honorarios(self, firm_id, hoje):
        d15 = hoje - datetime.timedelta(days=15)
        d30 = hoje - datetime.timedelta(days=30)
        d60 = hoje - datetime.timedelta(days=60)

        agg = ParcelaHonorario.objects.filter(
            honorario__firm_id=firm_id, status="PENDENTE"
        ).aggregate(
            av_t=Sum(Case(When(due_date__gte=hoje, then="amount"), output_field=DecimalField())),
            av_c=Sum(Case(When(due_date__gte=hoje, then=1), output_field=IntegerField())),
            d1_t=Sum(Case(When(due_date__gte=d15, due_date__lt=hoje, then="amount"), output_field=DecimalField())),
            d1_c=Sum(Case(When(due_date__gte=d15, due_date__lt=hoje, then=1), output_field=IntegerField())),
            d2_t=Sum(Case(When(due_date__gte=d30, due_date__lt=d15, then="amount"), output_field=DecimalField())),
            d2_c=Sum(Case(When(due_date__gte=d30, due_date__lt=d15, then=1), output_field=IntegerField())),
            d3_t=Sum(Case(When(due_date__gte=d60, due_date__lt=d30, then="amount"), output_field=DecimalField())),
            d3_c=Sum(Case(When(due_date__gte=d60, due_date__lt=d30, then=1), output_field=IntegerField())),
            d4_t=Sum(Case(When(due_date__lt=d60, then="amount"), output_field=DecimalField())),
            d4_c=Sum(Case(When(due_date__lt=d60, then=1), output_field=IntegerField())),
        )

        return {
            "a_vencer":     {"count": agg["av_c"] or 0, "total": float(agg["av_t"] or 0)},
            "dias_1_15":    {"count": agg["d1_c"] or 0, "total": float(agg["d1_t"] or 0)},
            "dias_16_30":   {"count": agg["d2_c"] or 0, "total": float(agg["d2_t"] or 0)},
            "dias_31_60":   {"count": agg["d3_c"] or 0, "total": float(agg["d3_t"] or 0)},
            "dias_60_mais": {"count": agg["d4_c"] or 0, "total": float(agg["d4_t"] or 0)},
        }

    def _build_aging_inadimplencia(self, firm_id, hoje):
        vencidas = (
            ParcelaHonorario.objects.filter(
                honorario__firm_id=firm_id,
                status="PENDENTE",
                due_date__lt=hoje,
            )
            .select_related("honorario")
            .order_by("due_date")
        )

        buckets = {
            "dias_1_15":    {"count": 0, "total": 0.0, "items": []},
            "dias_16_30":   {"count": 0, "total": 0.0, "items": []},
            "dias_31_60":   {"count": 0, "total": 0.0, "items": []},
            "dias_60_mais": {"count": 0, "total": 0.0, "items": []},
        }
        total = 0.0
        total_count = 0

        for parcela in vencidas:
            days = (hoje - parcela.due_date).days
            amount = float(parcela.amount)
            item = {"title": parcela.honorario.title, "days": days, "amount": amount}
            total += amount
            total_count += 1

            if days <= 15:
                b = "dias_1_15"
            elif days <= 30:
                b = "dias_16_30"
            elif days <= 60:
                b = "dias_31_60"
            else:
                b = "dias_60_mais"

            buckets[b]["count"] += 1
            buckets[b]["total"] += amount
            buckets[b]["items"].append(item)

        return {"total": total, "total_count": total_count, "buckets": buckets}
