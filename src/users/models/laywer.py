from django.db import models
from ..models.auth import User


class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    full_name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    oab_number = models.CharField(max_length=20)
    oab_state = models.CharField(max_length=2)
    phone = models.CharField(max_length=20)
    birth_date = models.DateField(null=True, blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)

    TAX_REGIME_CHOICES = [
        ("SIMPLES", "Simplified National Regime"),
        ("LUCRO_PRESUMIDO", "Presumed Profit"),
        ("LUCRO_REAL", "Actual Profit"),
        ("AUTONOMO_PF", "Self-employed (Individual)"),
    ]
    tax_regime = models.CharField(
        max_length=30, 
        choices=TAX_REGIME_CHOICES, 
        default="AUTONOMO_PF"
    )

    cep = models.CharField(max_length=9, blank=True)
    street = models.CharField(max_length=255, blank=True)
    number = models.CharField(max_length=20, blank=True)
    complement = models.CharField(max_length=100, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    
    office_type = models.CharField(
        max_length=20, 
        choices=[("HOME", "Home Office"), ("PHYSICAL", "Physical Office")],
        default="HOME"
    )
    practice_areas = models.JSONField(default=list)

    has_employees = models.BooleanField(default=False)

    average_monthly_income = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Average Income"
    )
    average_monthly_expense = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Average Expense"
    )

    INCOME_VARIABILITY_CHOICES = [
        ("LOW", "Low - Predictable"),
        ("MEDIUM", "Medium - Some variation"),
        ("HIGH", "High - Very variable"),
    ]
    income_variability = models.CharField(
        max_length=20, 
        choices=INCOME_VARIABILITY_CHOICES, 
        default="HIGH"
    )

    has_bank_connected = models.BooleanField(default=False)

    GOAL_TYPE_CHOICES = [
        ("SURVIVAL", "Survival - Pay off debts and keep the office operating"),
        ("STABILITY", "Stability - Build a solid and predictable financial practice"),
        ("GROWTH", "Growth - Scale the office and increase revenue"),
    ]
    goal_type = models.CharField(
        max_length=20, 
        choices=GOAL_TYPE_CHOICES, 
        default="STABILITY"
    )
    
    financial_goal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Monthly Financial Goal (Optional)"
    )

    onboarding_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} (OAB/{self.oab_state} {self.oab_number})"