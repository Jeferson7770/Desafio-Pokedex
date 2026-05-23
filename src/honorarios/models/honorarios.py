from django.db import models
from decimal import Decimal
from django.utils import timezone

class Honorario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        RECEBIDO = "RECEBIDO", "Recebido"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="fees")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor total do contrato/honorário")
    date = models.DateField(help_text="Data base do contrato ou primeiro vencimento")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    notes = models.TextField(blank=True, default="")
    
    is_installment = models.BooleanField(default=False, help_text="Flag indicando se é parcelado")
    total_installments = models.PositiveIntegerField(default=1, help_text="Quantidade total de parcelas")
    interest_rate_month = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), 
        help_text="Percentual de juros/multa por mês de atraso (Ex: 2.00 para 2%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.firm.name}) - R$ {self.amount}"


class ParcelaHonorario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        RECEBIDO = "RECEBIDO", "Recebido"

    honorario = models.ForeignKey(Honorario, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor específico desta parcela")
    due_date = models.DateField(help_text="Data de vencimento da parcela")
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