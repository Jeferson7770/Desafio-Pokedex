from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from django.db.models import Sum, Max, Min, QuerySet

@dataclass(frozen=True)
class ExpenseComposition:
    fixed: float
    variable: float
    eventual: float

@dataclass(frozen=True)
class ExpenseCategories:
    payroll: float
    taxes: float
    structure: float

@dataclass(frozen=True)
class SeasonalityData:
    months: List[str]
    values: List[float]
    months_count: int
    highest_volume: float
    lowest_volume: float

@dataclass(frozen=True)
class ProfitDistribution:
    percentage: float
    value: float

@dataclass(frozen=True)
class PayrollSummary:
    total_payroll: float
    monthly_average: float
    team_size: int
    revenue_commitment_percentage: float

@dataclass(frozen=True)
class CashFlowReportPayload:
    total_revenue: float
    total_expense: float
    net_result: float
    profit_margin: float
    expense_composition: ExpenseComposition
    expense_categories: ExpenseCategories
    late_interest_total: float
    seasonality: SeasonalityData
    distribution_to_partners: ProfitDistribution
    payroll_summary: PayrollSummary

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CashFlowEngine:
    """
    Engine responsável por encapsular regras de negócio e métricas analíticas
    do fluxo de caixa consolidadas a partir de dados históricos (Open Finance).
    """

    MONTHS_MAP = {
        1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
        7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ"
    }

    def __init__(self, queryset: Any):
        if hasattr(queryset, "pk") and not isinstance(queryset, QuerySet):
            self.queryset = queryset.__class__.objects.filter(pk=queryset.pk)
        else:
            self.queryset = queryset
            
        self.aggregates = self._calculate_base_aggregates()

    def _calculate_base_aggregates(self) -> Dict[str, Any]:
        return self.queryset.aggregate(
            rev=Sum('total_revenue'),
            exp=Sum('total_expense'),
            fixed=Sum('expenses_fixed'),
            var=Sum('expenses_variable'),
            eventual=Sum('expenses_eventual'),
            payroll=Sum('expenses_payroll'),
            taxes=Sum('expenses_taxes'),
            structure=Sum('expenses_structure'),
            interest=Sum('expenses_late_interest'),
            max_team=Max('team_size'),
            max_rev=Max('total_revenue'),
            min_rev=Min('total_revenue')
        )

    def _safe_percentage(self, part: float, total: float, precision: int = 1) -> float:
        if not total or total <= 0:
            return 0.0
        return round((part / total) * 100, precision)

    def get_vision_overview(self) -> tuple:
        rev = float(self.aggregates['rev'] or 0.0)
        exp = float(self.aggregates['exp'] or 0.0)
        net = rev - exp
        margin = self._safe_percentage(net, rev, precision=2)
        return rev, exp, net, margin

    def get_expense_composition(self) -> ExpenseComposition:
        fixed = float(self.aggregates['fixed'] or 0.0)
        var = float(self.aggregates['var'] or 0.0)
        ev = float(self.aggregates['eventual'] or 0.0)
        total = fixed + var + ev

        return ExpenseComposition(
            fixed=self._safe_percentage(fixed, total),
            variable=self._safe_percentage(var, total),
            eventual=self._safe_percentage(ev, total)
        )

    def get_expense_categories(self) -> ExpenseCategories:
        payroll = float(self.aggregates['payroll'] or 0.0)
        taxes = float(self.aggregates['taxes'] or 0.0)
        structure = float(self.aggregates['structure'] or 0.0)
        total = payroll + taxes + structure

        return ExpenseCategories(
            payroll=self._safe_percentage(payroll, total),
            taxes=self._safe_percentage(taxes, total),
            structure=self._safe_percentage(structure, total)
        )

    def get_seasonality(self) -> SeasonalityData:
        ordered_data = self.queryset.order_by('year', 'month')
        months_list = [self.MONTHS_MAP[item.month] for item in ordered_data]
        values_list = [float(item.total_revenue) for item in ordered_data]

        return SeasonalityData(
            months=months_list,
            values=values_list,
            months_count=len(values_list),
            highest_volume=float(self.aggregates['max_rev'] or 0.0),
            lowest_volume=float(self.aggregates['min_rev'] or 0.0)
        )

    def get_payroll_summary(self, total_revenue: float) -> PayrollSummary:
        payroll = float(self.aggregates['payroll'] or 0.0)
        months_count = self.queryset.count() or 1
        
        return PayrollSummary(
            total_payroll=payroll,
            monthly_average=round(payroll / months_count, 2),
            team_size=int(self.aggregates['max_team'] or 0),
            revenue_commitment_percentage=self._safe_percentage(payroll, total_revenue)
        )

    def generate_full_report(self) -> CashFlowReportPayload:
        """Gera o payload estruturado completo aplicando os contratos de dados."""
        rev, exp, net, margin = self.get_vision_overview()
        
        partner_percentage = 15.0
        partner_value = round((net * partner_percentage) / 100, 2) if net > 0 else 0.0

        return CashFlowReportPayload(
            total_revenue=rev,
            total_expense=exp,
            net_result=net,
            profit_margin=margin,
            expense_composition=self.get_expense_composition(),
            expense_categories=self.get_expense_categories(),
            late_interest_total=float(self.aggregates['interest'] or 0.0),
            seasonality=self.get_seasonality(),
            distribution_to_partners=ProfitDistribution(percentage=partner_percentage, value=partner_value),
            payroll_summary=self.get_payroll_summary(rev)
        )