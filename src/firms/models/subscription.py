from django.db import models
from ..models.firm_structure import Firm

class Plan(models.Model):
    class CycleType(models.TextChoices):
        WEEKLY = "WEEKLY", "Semanal"
        MONTHLY = "MONTHLY", "Mensal"
        SEMIANNUALLY = "SEMIANNUALLY", "Semestral"
        ANNUALLY = "ANNUALLY", "Anual"

    name = models.CharField(max_length=100)
    abacatepay_product_id = models.CharField(max_length=255, unique=True, help_text="ID do produto gerado no painel do AbacatePay")
    cycle = models.CharField(max_length=20, choices=CycleType.choices, default=CycleType.MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_cycle_display()})"


class FirmSubscription(models.Model):
    class SubscriptionStatus(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        ACTIVE = "ACTIVE", "Ativa"
        EXPIRED = "EXPIRED", "Expirada"
        CANCELLED = "CANCELLED", "Cancelada"

    firm = models.OneToOneField(Firm, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    abacatepay_billing_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.PENDING)
    current_period_end = models.DateTimeField(blank=True, null=True, help_text="Data de expiração do ciclo atual")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assinatura do escritório {self.firm.name} - Status: {self.status}"