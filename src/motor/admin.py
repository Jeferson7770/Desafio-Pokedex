from django.contrib import admin

from .models import MotorPrioridade

@admin.register(MotorPrioridade)
class MotorPrioridadeAdmin(admin.ModelAdmin):
    list_display = ("id", "prioridade", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("prioridade",)
