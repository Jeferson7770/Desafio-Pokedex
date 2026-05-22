from django.db import models
from django.utils import timezone

class Expense(models.Model):
    class Frequency(models.TextChoices):
        ONE_TIME = "ONE_TIME", "Única"
        MONTHLY = "MONTHLY", "Mensal"
        YEARLY = "ANNUAL", "Anual"

    class Category(models.TextChoices):
        ESTRUTURA = "ESTRUTURA", "Estrutura"
        PESSOAS = "PESSOAS", "Pessoas"
        IMPOSTOS = "IMPOSTOS", "Impostos"
        OPERACIONAL = "OPERACIONAL", "Operacional"

    class Priority(models.TextChoices):
        LEGAL = "LEGAL", "Legal / Crítico"
        OPERACIONAL = "OPERACIONAL", "Operacional"
        OPCIONAL = "OPCIONAL", "Opcional"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="expenses")
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.ONE_TIME)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OPERACIONAL)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.OPERACIONAL)
    
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateField(null=True, blank=True, verbose_name="Data do Pagamento")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.firm.name}) - R$ {self.amount}"

    @property
    def status(self):
        """
        Retorna o status dinâmico com base no pagamento e na data atual.
        """
        if self.is_paid:
            return "PAGO"
        
        if self.due_date < timezone.localdate():
            return "VENCIDO"
            
        return "A_VENCER"