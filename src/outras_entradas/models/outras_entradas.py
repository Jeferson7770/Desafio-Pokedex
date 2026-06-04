from decimal import Decimal
from django.db import models


class OutraEntrada(models.Model):
    class Status(models.TextChoices):
        RECEBIDO = "RECEBIDO", "Recebido"
        PENDENTE = "PENDENTE", "Pendente"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="outras_entradas")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    notes = models.TextField(blank=True, default="")
    is_installment = models.BooleanField(default=False)
    total_installments = models.PositiveIntegerField(default=1)
    installment_value = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate_month = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.firm.name})"


class OutraEntradaInstallment(models.Model):
    class Status(models.TextChoices):
        RECEBIDO = "RECEBIDO", "Recebido"
        PENDENTE = "PENDENTE", "Pendente"

    outra_entrada = models.ForeignKey(OutraEntrada, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    late_interest_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["installment_number"]
