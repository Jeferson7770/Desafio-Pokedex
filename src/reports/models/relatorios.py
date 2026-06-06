from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class FinancialReportSummary(models.Model):
    firm = models.ForeignKey(
        'firms.Firm', 
        on_delete=models.CASCADE, 
        related_name="financial_summaries"
    )
    
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    expenses_fixed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    expenses_variable = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    expenses_eventual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    expenses_payroll = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="People/Payroll")
    expenses_taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Taxes")
    expenses_structure = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Structure/Office")
    expenses_late_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Late Interest")

    team_size = models.IntegerField(default=0)

    last_sync_at = models.DateTimeField(null=True, blank=True)
    is_fully_categorized = models.BooleanField(default=False)

    class Meta:
        unique_together = ('firm', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.firm.name} - {self.month:02d}/{self.year}"

    @property
    def net_result(self):
        return self.total_revenue - self.total_expense

    @property
    def profit_margin(self):
        if self.total_revenue <= 0:
            return 0
        return (self.net_result / self.total_revenue) * 100