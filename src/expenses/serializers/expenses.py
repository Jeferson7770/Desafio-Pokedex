from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
import datetime
from ..models.expenses import Expense, ParcelaDespesa
from ..models.expenses_deferral import ExpenseDeferral

class ExpenseDeferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseDeferral
        fields = ["id", "original_date", "new_date", "penalty_amount", "created_at"]


class ParcelaDespesaSerializer(serializers.ModelSerializer):
    late_interest_cost = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    deferrals = ExpenseDeferralSerializer(many=True, read_only=True)

    class Meta:
        model = ParcelaDespesa
        fields = ["id", "installment_number", "amount", "due_date", "is_paid", "paid_at", "status", "late_interest_cost", "deferrals"]


class ExpenseSerializer(serializers.ModelSerializer):
    installments = ParcelaDespesaSerializer(many=True, read_only=True)
    installment_value = serializers.SerializerMethodField()
    
    category_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id", "firm", "title", "description", "amount", "due_date",
            "frequency", "category", "category_display", "priority", 
            "priority_display", "is_paid", "paid_at", "is_active", 
            "is_installment", "total_installments", "installment_value",
            "interest_rate_month", "installments", "created_at",
        ]
        read_only_fields = ["firm", "paid_at"]

    def get_installment_value(self, obj) -> float:
        if obj.total_installments > 0:
            return round(float(obj.amount) / obj.total_installments, 2)
        return float(obj.amount)

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_priority_display(self, obj):
        return obj.get_priority_display()

    def create(self, validated_data):
        expense = Expense.objects.create(**validated_data)
        
        total_amount = expense.amount
        installments_count = expense.total_installments if expense.is_installment else 1
        base_amount = (total_amount / installments_count).quantize(Decimal("0.01"))
        diff = total_amount - (base_amount * installments_count)

        base_date = expense.due_date

        for i in range(1, installments_count + 1):
            installment_amount = base_amount
            if i == installments_count:
                installment_amount += diff
            
            months_to_add = i - 1
            year_offset = (base_date.month + months_to_add - 1) // 12
            new_month = (base_date.month + months_to_add - 1) % 12 + 1
            new_year = base_date.year + year_offset
            
            try:
                due_date = datetime.date(new_year, new_month, base_date.day)
            except ValueError:
                next_month = new_month % 12 + 1
                next_year = new_year + (1 if new_month == 12 else 0)
                due_date = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)

            ParcelaDespesa.objects.create(
                expense=expense,
                installment_number=i,
                amount=installment_amount,
                due_date=due_date,
                is_paid=expense.is_paid,
                paid_at=expense.paid_at if expense.is_paid else None
            )
            
        return expense

    def update(self, instance, validated_data):
        is_paid = validated_data.get("is_paid", instance.is_paid)
        if is_paid and not instance.is_paid:
            instance.paid_at = timezone.localdate()
            instance.installments.all().update(is_paid=True, paid_at=timezone.localdate())
        elif not is_paid:
            instance.paid_at = None
            instance.installments.all().update(is_paid=False, paid_at=None)
            
        return super().update(instance, validated_data)