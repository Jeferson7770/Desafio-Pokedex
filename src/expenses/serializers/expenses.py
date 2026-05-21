from rest_framework import serializers
from django.utils import timezone
from ..models.expenses import Expense
from ..models.expenses_deferral import ExpenseDeferral

class ExpenseDeferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseDeferral
        fields = ["id", "original_date", "new_date", "penalty_amount", "created_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    deferrals = ExpenseDeferralSerializer(many=True, read_only=True)
    status = serializers.ReadOnlyField()
    
    category_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id", "firm", "title", "description", "amount", "due_date",
            "frequency", "category", "category_display", "priority", 
            "priority_display", "is_paid", "paid_at", "status", 
            "is_active", "deferrals", "created_at",
        ]
        read_only_fields = ["firm", "paid_at"]

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_priority_display(self, obj):
        return obj.get_priority_display()

    def update(self, instance, validated_data):
        is_paid = validated_data.get("is_paid", instance.is_paid)
        if is_paid and not instance.is_paid:
            instance.paid_at = timezone.localdate()
        elif not is_paid:
            instance.paid_at = None
            
        return super().update(instance, validated_data)