from django.db import models

class Honorario(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        RECEBIDO = "RECEBIDO", "Recebido"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="fees")
    
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.firm.name}) - R$ {self.amount}"