from django.db import models
from ..models.firm_structure import Firm

class Plan(models.Model):
    class CycleType(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        SEMIANNUALLY = "SEMIANNUALLY", "Semiannual"
        ANNUALLY = "ANNUALLY", "Annual"

    name = models.CharField(max_length=100)
    abacatepay_product_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Product ID generated in the AbacatePay dashboard")
    stripe_price_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Stripe Price ID (price_*)")
    cycle = models.CharField(max_length=20, choices=CycleType.choices, default=CycleType.MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_cycle_display()})"


class FirmSubscription(models.Model):
    class SubscriptionStatus(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    firm = models.OneToOneField(Firm, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions", null=True, blank=True)
    abacatepay_billing_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="Stripe Subscription ID (sub_*)")
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Customer ID (cus_*)")
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIAL)
    trial_ends_at = models.DateTimeField(blank=True, null=True, help_text="End of free trial period")
    current_period_end = models.DateTimeField(blank=True, null=True, help_text="Current cycle expiration date")
    cancel_reason = models.CharField(max_length=50, blank=True, null=True, help_text="Motivo selecionado no cancelamento")
    cancel_feedback = models.TextField(blank=True, null=True, help_text="Texto livre do cancelamento")
    cancelled_at = models.DateTimeField(blank=True, null=True, help_text="Quando o cancelamento foi solicitado")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription for firm {self.firm.name} - Status: {self.status}"