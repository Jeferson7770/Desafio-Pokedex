from django.db import models
from decimal import Decimal

class BankAccount(models.Model):
    class AccountType(models.TextChoices):
        CHECKING = "CHECKING", "Checking Account"
        SAVINGS = "SAVINGS", "Savings"
        INVESTMENT = "INVESTMENT", "Investments"
        CASH = "CASH", "Cash"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="bank_accounts")
    name = models.CharField(max_length=100, help_text="Example: Office Bank, Shared Cash Box")
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.CHECKING)
    
    provider_name = models.CharField(max_length=100, blank=True, help_text="Bank name in Open Finance (example: Bradesco)")
    external_account_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Account ID in the Open Finance API")
    
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.firm.name}) - R$ {self.current_balance}"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INFLOW = "INFLOW", "Income (Inflow)"
        OUTFLOW = "OUTFLOW", "Expense (Outflow)"

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transactions")
    
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    date = models.DateField(help_text="Financial settlement date")
    
    expense_installment = models.ForeignKey(
        "expenses.ParcelaDespesa", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="transactions"
    )
    fee_installment = models.ForeignKey(
        "honorarios.ParcelaHonorario", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="transactions"
    )

    external_transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Transaction ID in the Open Finance statement")
    is_reconciled = models.BooleanField(default=False, help_text="Indicates whether the bank transaction has been reconciled with the system")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        sign = "+" if self.transaction_type == self.TransactionType.INFLOW else "-"
        return f"[{self.date}] {sign}R$ {self.amount} - {self.description}"