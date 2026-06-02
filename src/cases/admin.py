from django.contrib import admin

from .models.case_payment import CasePaymentSchedule
from .models.case_structure import Client, Process


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ("name", "type", "cpf_cnpj", "phone", "email", "firm", "created_at")
	list_filter = ("type", "firm")
	search_fields = ("name", "cpf_cnpj", "email", "phone")


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
	list_display = ("title", "client_name", "status", "payment_type", "total_fee", "firm", "created_at")
	list_filter = ("status", "payment_type", "firm")
	search_fields = ("title", "client_name")


@admin.register(CasePaymentSchedule)
class CasePaymentScheduleAdmin(admin.ModelAdmin):
	list_display = ("case", "amount", "expected_date", "probability", "paid")
	list_filter = ("paid",)
