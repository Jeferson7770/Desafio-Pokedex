import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Sum, Case, When, DecimalField
from django.db.models.functions import TruncMonth
from ..models.relatorios import FinancialReportSummary
from ..serializers.relatorios import FinancialReportDashboardSerializer
from ...fees.models.honorarios import ParcelaHonorario
from ...expenses.models.expenses import Expense, ParcelaDespesa
from ...other_income.models.outras_entradas import OutraEntradaInstallment
from ...firms.models.firm_member import FirmMember
from ...users.utils.telemetry import track_event
from ...users.utils.firm_mixin import FirmMixin

MONTHS_PT = {1:"JAN",2:"FEV",3:"MAR",4:"ABR",5:"MAI",6:"JUN",
             7:"JUL",8:"AGO",9:"SET",10:"OUT",11:"NOV",12:"DEZ"}

_PAYROLL_CATS = {Expense.Category.PESSOAL_E_REMUNERACAO, Expense.Category.PESSOAS}
_TAX_CATS     = {Expense.Category.FISCAL_E_OBRIGACOES_LEGAIS, Expense.Category.IMPOSTOS,
                 Expense.Category.FINANCEIRA}
_VARIABLE_CATS = {Expense.Category.CUSTAS_PROCESSUAIS_E_JUDICIAIS,
                  Expense.Category.MOBILIDADE_E_DESLOCAMENTO}


class FinancialReportViewSet(FirmMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = FinancialReportSummary.objects.all()
    serializer_class = FinancialReportDashboardSerializer

    def get_queryset(self):
        firm_id = self._get_firm_id()
        if not firm_id:
            return self.queryset.none()
        return self.queryset.filter(firm_id=firm_id)

    def list(self, request, *args, **kwargs):
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError({"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."})

        now = timezone.now()
        try:
            year  = int(request.query_params.get("year",  now.year))
            month = int(request.query_params.get("month", now.month))
        except ValueError:
            raise ValidationError({"detail": "Os parâmetros 'year' e 'month' devem ser inteiros válidos."})

        cache_key = f"financial_report:{firm_id}:{year}:{month}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        hoje = timezone.localdate()
        start = datetime.date(year, month, 1)
        end   = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

        hon_rec = ParcelaHonorario.objects.filter(
            honorario__firm_id=firm_id, status="RECEBIDO",
            due_date__gte=start, due_date__lt=end,
        ).aggregate(t=Sum("amount"))["t"] or 0

        outras_rec = OutraEntradaInstallment.objects.filter(
            outra_entrada__firm_id=firm_id, status="RECEBIDO",
            due_date__gte=start, due_date__lt=end,
        ).aggregate(t=Sum("amount"))["t"] or 0

        total_revenue = float(hon_rec) + float(outras_rec)

        parcelas_pagas = list(
            ParcelaDespesa.objects.filter(
                expense__firm_id=firm_id, expense__is_active=True,
                due_date__gte=start, due_date__lt=end, is_paid=True,
            ).select_related("expense")
        )

        total_expense = sum(float(p.amount) for p in parcelas_pagas)

        fixed = variable = eventual = 0.0
        payroll = taxes = structure = 0.0
        for p in parcelas_pagas:
            amt = float(p.amount)
            cat = p.expense.category
            freq = p.expense.frequency

            if cat in _VARIABLE_CATS:
                variable += amt
            elif freq == Expense.Frequency.MONTHLY:
                fixed += amt
            else:
                eventual += amt

            if cat in _PAYROLL_CATS:
                payroll += amt
            elif cat in _TAX_CATS:
                taxes += amt
            else:
                structure += amt

        def pct(part, total):
            return round(part / total * 100, 1) if total > 0 else 0.0

        overdue = ParcelaDespesa.objects.filter(
            expense__firm_id=firm_id, expense__is_active=True,
            is_paid=False, due_date__lt=hoje,
        ).select_related("expense")
        late_interest_total = sum(float(p.late_interest_cost) for p in overdue)

        m12 = month - 11
        y12 = year
        if m12 <= 0:
            m12 += 12
            y12 -= 1
        twelve_start = datetime.date(y12, m12, 1)

        hon_mensal = (
            ParcelaHonorario.objects.filter(
                honorario__firm_id=firm_id, status="RECEBIDO",
                due_date__gte=twelve_start, due_date__lt=end,
            )
            .annotate(mes=TruncMonth("due_date"))
            .values("mes").annotate(total=Sum("amount"))
        )
        outras_mensal = (
            OutraEntradaInstallment.objects.filter(
                outra_entrada__firm_id=firm_id, status="RECEBIDO",
                due_date__gte=twelve_start, due_date__lt=end,
            )
            .annotate(mes=TruncMonth("due_date"))
            .values("mes").annotate(total=Sum("amount"))
        )

        rev_map: dict[str, float] = {}
        for row in hon_mensal:
            k = row["mes"].strftime("%Y-%m")
            rev_map[k] = rev_map.get(k, 0.0) + float(row["total"] or 0)
        for row in outras_mensal:
            k = row["mes"].strftime("%Y-%m")
            rev_map[k] = rev_map.get(k, 0.0) + float(row["total"] or 0)

        season_months, season_values = [], []
        for i in range(12):
            mi = m12 + i
            yi = y12
            if mi > 12:
                mi -= 12
                yi += 1
            k = f"{yi}-{mi:02d}"
            season_months.append(MONTHS_PT[mi])
            season_values.append(rev_map.get(k, 0.0))

        payroll_total_period = sum(
            float(p.amount) for p in parcelas_pagas if p.expense.category in _PAYROLL_CATS
        )
        team_size = FirmMember.objects.filter(firm_id=firm_id).count()

        net_result    = total_revenue - total_expense
        profit_margin = pct(net_result, total_revenue)
        partner_pct   = 15.0
        partner_value = round(net_result * partner_pct / 100, 2) if net_result > 0 else 0.0

        result = {
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_result": net_result,
            "profit_margin": profit_margin,
            "expense_composition": {
                "fixed":    pct(fixed,    total_expense),
                "variable": pct(variable, total_expense),
                "eventual": pct(eventual, total_expense),
            },
            "expense_categories": {
                "payroll":   pct(payroll,   total_expense),
                "taxes":     pct(taxes,     total_expense),
                "structure": pct(structure, total_expense),
            },
            "late_interest_total": round(late_interest_total, 2),
            "seasonality": {
                "months":         season_months,
                "values":         season_values,
                "months_count":   len([v for v in season_values if v > 0]),
                "highest_volume": max(season_values) if season_values else 0.0,
                "lowest_volume":  min((v for v in season_values if v > 0), default=0.0),
            },
            "distribution_to_partners": {
                "percentage": partner_pct,
                "value":      partner_value,
            },
            "payroll_summary": {
                "total_payroll":                  payroll_total_period,
                "monthly_average":                round(payroll_total_period, 2),
                "team_size":                      team_size,
                "revenue_commitment_percentage":  pct(payroll_total_period, total_revenue),
            },
        }

        cache.set(cache_key, result, timeout=300)

        track_event(
            user=request.user,
            event_name="relatorio_financeiro_visualizado",
            properties={"ano_relatorio": year, "mes_relatorio": month,
                        "total_revenue": total_revenue, "total_expense": total_expense},
        )

        return Response(result, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        firm_id = self._get_firm_id()
        if not firm_id:
            raise ValidationError({"detail": "O usuário autenticado não possui uma empresa/firma vinculada ao seu perfil."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        year = serializer.validated_data.get('year')
        month = serializer.validated_data.get('month')

        instance, created = FinancialReportSummary.objects.update_or_create(
            firm_id=firm_id,
            year=year,
            month=month,
            defaults=serializer.validated_data,
        )
        cache.delete(f"financial_report:{firm_id}:{year}:{month}")

        track_event(
            user=user,
            event_name="relatorio_financeiro_consolidado",
            properties={
                "report_id": instance.id if instance.id else None,
                "ano_relatorio": year,
                "mes_relatorio": month,
                "acao": "criado" if created else "atualizado",
                "total_revenue": float(instance.total_revenue),
                "total_expense": float(instance.total_expense)
            }
        )

        response_serializer = self.get_serializer(instance)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )