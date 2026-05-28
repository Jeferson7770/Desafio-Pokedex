from django.contrib import admin

from .models import SimulacaoPrioridade

@admin.register(SimulacaoPrioridade)
class SimulacaoPrioridadeAdmin(admin.ModelAdmin):
    list_display = ("id", "reference_date", "saldo_total_disponivel", "saldo_restante_pos_pagamentos", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("reference_date",)
