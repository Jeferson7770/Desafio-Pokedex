from rest_framework import serializers
from src.expenses.models import Expense, ExpenseDeferral


class ExpenseDeferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseDeferral
        fields = ["id", "original_date", "new_date", "penalty_amount", "created_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    deferrals = ExpenseDeferralSerializer(many=True, read_only=True)
    status = serializers.ReadOnlyField()
    
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "firm",
            "title",
            "description",
            "amount",
            "due_date",
            "frequency",
            "category",
            "category_display",
            "priority",
            "priority_display",
            "is_paid",
            "paid_at",
            "status",
            "is_active",
            "deferrals",
            "created_at",
        ]
        read_only_fields = ["firm", "paid_at"]

    def update(self, instance, validated_data):
        """
        Garante que ao marcar 'is_paid' como True via API, 
        o 'paid_at' seja preenchido automaticamente com a data de hoje.
        """
        is_paid = validated_data.get("is_paid", instance.is_paid)
        if is_paid and not instance.is_paid:
            from django.utils import timezone
            instance.paid_at = timezone.localdate()
        elif not is_paid:
            instance.paid_at = None
            
        return super().update(instance, validated_data)