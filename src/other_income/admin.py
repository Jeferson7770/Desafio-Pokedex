from django.contrib import admin
from .models.outras_entradas import OutraEntrada, OutraEntradaInstallment


@admin.register(OutraEntrada)
class OutraEntradaAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "firm", "amount", "date", "status", "is_installment")
    list_filter = ("status", "is_installment", "firm")
    search_fields = ("title",)


@admin.register(OutraEntradaInstallment)
class OutraEntradaInstallmentAdmin(admin.ModelAdmin):
    list_display = ("id", "outra_entrada", "installment_number", "amount", "due_date", "status")
    list_filter = ("status",)
