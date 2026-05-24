from django.db import models
from django.conf import settings

class Plan(models.Model):
    INTERVAL_CHOICES = [
        ("MONTHLY", "Mensal"),
        ("ANNUAL", "Anual"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES, default="MONTHLY")
    is_active = models.BooleanField(default=True)
    
    gateway_plan_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.name} - R$ {self.price}/{self.interval}"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Ativa"),
        ("CANCELED", "Cancelada"),
        ("PAST_DUE", "Inadimplente (Erro de pagamento)"),
        ("TRIALING", "Período de Testes"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    
    cancel_at_period_end = models.BooleanField(default=False)

    gateway_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    gateway_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assinatura de {self.user.email} - Status: {self.status}"

    @property
    def is_valid(self):
        """
        Dita se o advogado tem direito a usar os recursos PRO do app.
        Mesmo se estiver cancelado, se ainda estiver dentro do prazo pago, ele acessa.
        """
        from django.utils import timezone
        if self.status in ["ACTIVE", "TRIALING"]:
            return True
        if self.status == "CANCELED" and self.current_period_end > timezone.now():
            return True
        return False