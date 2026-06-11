from django.db import models


class Client(models.Model):
    class Tipo(models.TextChoices):
        PF = "PF", "Individual"
        PJ = "PJ", "Legal Entity"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="clients")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    cpf_cnpj = models.CharField(max_length=18, blank=True, default="")
    type = models.CharField(max_length=2, choices=Tipo.choices, default=Tipo.PF)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Process(models.Model):
    class PaymentType(models.TextChoices):
        FIXED = "FIXED"
        INSTALLMENT = "INSTALLMENT"
        SUCCESS_FEE = "SUCCESS_FEE"
        HYBRID = "HYBRID"

    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Active"
        CONCLUIDO = "CONCLUIDO", "Completed"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="cases")
    client = models.ForeignKey("cases.Client", on_delete=models.SET_NULL, related_name="processes", null=True, blank=True)

    client_name = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)

    total_fee = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)

    win_probability = models.FloatField(default=1.0)

    stage = models.CharField(max_length=100, null=True, blank=True)

    expected_close_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.client_id:
            self.client_name = self.client.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


Case = Process
