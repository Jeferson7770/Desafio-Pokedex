from django.db import models
from decimal import Decimal
from django.utils import timezone

class Honorario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pending"
        RECEBIDO = "RECEBIDO", "Received"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="fees")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total contract/fee amount")
    date = models.DateField(help_text="Contract base date or first due date")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    notes = models.TextField(blank=True, default="")
    
    is_installment = models.BooleanField(default=False, help_text="Indicates whether this fee is paid in installments")
    total_installments = models.PositiveIntegerField(default=1, help_text="Total number of installments")
    interest_rate_month = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), 
        help_text="Monthly late interest/penalty percentage (example: 2.00 for 2%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.firm.name}) - R$ {self.amount}"


class ParcelaHonorario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pending"
        RECEBIDO = "RECEBIDO", "Received"

    honorario = models.ForeignKey(Honorario, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Specific amount for this installment")
    due_date = models.DateField(help_text="Installment due date")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["installment_number"]

    @property
    def late_interest_cost(self) -> Decimal:
        """
        Calcula o custo acumulado de juros caso a parcela esteja atrasada.
        Juros Simples pro-rata die com base na taxa mensal informada no contrato.
        """
        if self.status == self.Status.RECEBIDO or self.due_date >= timezone.now().date():
            return Decimal("0.00")
        
        days_late = (timezone.now().date() - self.due_date).days
        daily_rate = (self.honorario.interest_rate_month / Decimal("100.00")) / Decimal("30")
        
        interest_accumulated = self.amount * daily_rate * Decimal(days_late)
        return interest_accumulated.quantize(Decimal("0.01"))