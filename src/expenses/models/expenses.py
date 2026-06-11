from django.db import models
from django.utils import timezone
from decimal import Decimal

class Expense(models.Model):
    class Frequency(models.TextChoices):
        ONE_TIME = "ONE_TIME", "One-time"
        MONTHLY = "MONTHLY", "Monthly"
        YEARLY = "ANNUAL", "Annual"

    class Category(models.TextChoices):
        PESSOAL_E_REMUNERACAO = "PESSOAL_E_REMUNERACAO", "Pessoal e Remuneração"
        CUSTAS_PROCESSUAIS_E_JUDICIAIS = "CUSTAS_PROCESSUAIS_E_JUDICIAIS", "Custas Processuais e Judiciais"
        FINANCEIRA = "FINANCEIRA", "Financeira"
        CAPACITACAO_E_DESENVOLVIMENTO = "CAPACITACAO_E_DESENVOLVIMENTO", "Capacitação e Desenvolvimento"
        FISCAL_E_OBRIGACOES_LEGAIS = "FISCAL_E_OBRIGACOES_LEGAIS", "Fiscal e Obrigações Legais"
        ESTRUTURA_E_OPERACAO = "ESTRUTURA_E_OPERACAO", "Estrutura e Operação"
        TECNOLOGIA_E_ASSINATURA = "TECNOLOGIA_E_ASSINATURA", "Tecnologia e Assinatura"
        MARKETING_E_AQUISICAO = "MARKETING_E_AQUISICAO", "Marketing e Aquisição"
        MOBILIDADE_E_DESLOCAMENTO = "MOBILIDADE_E_DESLOCAMENTO", "Mobilidade e Deslocamento"
        INVESTIMENTOS_NO_ESCRITORIO = "INVESTIMENTOS_NO_ESCRITORIO", "Investimentos no Escritório"
        A_CLASSIFICAR = "A_CLASSIFICAR", "A Classificar"

        ESTRUTURA = "ESTRUTURA", "Estrutura"
        PESSOAS = "PESSOAS", "Pessoas"
        IMPOSTOS = "IMPOSTOS", "Impostos"
        OPERACIONAL = "OPERACIONAL", "Operacional"

    class Priority(models.TextChoices):
        LEGAL = "LEGAL", "Legal / Critical"
        OPERACIONAL = "OPERACIONAL", "Operational"
        OPCIONAL = "OPCIONAL", "Optional"

    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="expenses")
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total expense amount")
    due_date = models.DateField(help_text="Base date or first due date")
    
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.ONE_TIME)
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.OPERACIONAL)
    subcategory = models.CharField(max_length=100, blank=True, default="")
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.OPERACIONAL)
    
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    is_installment = models.BooleanField(default=False)
    total_installments = models.PositiveIntegerField(default=1)
    interest_rate_month = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.title} ({self.firm.name}) - R$ {self.amount}"


class ParcelaDespesa(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["installment_number"]

    @property
    def status(self):
        if self.is_paid:
            return "PAGO"
        if self.due_date < timezone.localdate():
            return "VENCIDO"
        return "A_VENCER"

    @property
    def late_interest_cost(self) -> Decimal:
        """Calcula o juro acumulado pro-rata se a parcela estiver vencida."""
        if self.is_paid or self.due_date >= timezone.localdate():
            return Decimal("0.00")
        
        days_late = (timezone.localdate() - self.due_date).days
        daily_rate = (self.expense.interest_rate_month / Decimal("100.00")) / Decimal("30")
        return (self.amount * daily_rate * Decimal(days_late)).quantize(Decimal("0.01"))