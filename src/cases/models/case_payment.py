from django.db import models

class CasePaymentSchedule(models.Model):
    case = models.ForeignKey("cases.Process", on_delete=models.CASCADE, related_name="schedules")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expected_date = models.DateField()

    probability = models.FloatField(default=1.0)

    paid = models.BooleanField(default=False)