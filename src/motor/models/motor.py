from django.db import models
from decimal import Decimal

class SimulacaoPrioridade(models.Model):
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="prioritization_simulations")
    reference_date = models.DateField(help_text="Mês/Ano de referência da simulação (usar dia 1 do mês)")
    
    saldo_total_disponivel = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    saldo_restante_pos_pagamentos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Simulação de Prioridade"
        verbose_name_plural = "Simulações de Prioridade"

    def __str__(self):
        return f"Simulação {self.reference_date.strftime('%m/%Y')} - {self.firm.name}"


class ItemSimulacaoPrioridade(models.Model):
    class StatusRecomendacao(models.TextChoices):
        RECOMENDADO = "RECOMENDADO", "Pagamento Recomendado"
        NAO_COBERTO = "NAO_COBERTO", "Não Coberto pelo Saldo"

    simulacao = models.ForeignKey(SimulacaoPrioridade, on_delete=models.CASCADE, related_name="items")
    parcela = models.ForeignKey("expenses.ParcelaDespesa", on_delete=models.CASCADE, related_name="simulation_appearances")
    status_recomendacao = models.CharField(max_length=20, choices=StatusRecomendacao.choices)
    amount_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    late_interest_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    
    ordem = models.PositiveIntegerField(default=0, help_text="Posição do card na tela")

    class Meta:
        unique_together = ("simulacao", "parcela")
        ordering = ["ordem"]