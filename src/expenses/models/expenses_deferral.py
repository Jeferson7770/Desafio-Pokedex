from django.db import models
from .expenses import ParcelaDespesa

class ExpenseDeferral(models.Model):
    installment = models.ForeignKey(ParcelaDespesa, on_delete=models.CASCADE, related_name="deferrals")
    original_date = models.DateField()
    new_date = models.DateField()
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adiamento da Parcela {self.installment.installment_number}: {self.original_date} -> {self.new_date}"