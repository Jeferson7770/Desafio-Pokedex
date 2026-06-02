from rest_framework import serializers
from ..models.honorarios import Honorario, ParcelaHonorario
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class ParcelaHonorarioSerializer(serializers.ModelSerializer):
    late_interest_cost = serializers.ReadOnlyField()

    class Meta:
        model = ParcelaHonorario
        fields = ["id", "installment_number", "amount", "due_date", "status", "late_interest_cost", "paid_at"]


class HonorarioSerializer(serializers.ModelSerializer):
    installments = ParcelaHonorarioSerializer(many=True, read_only=True)
    installment_value = serializers.SerializerMethodField()

    class Meta:
        model = Honorario
        fields = [
            "id", "title", "amount", "date", "status", "notes", 
            "is_installment", "total_installments", "installment_value",
            "interest_rate_month", "installments", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def get_installment_value(self, obj) -> float:
        if obj.total_installments > 0:
            return round(float(obj.amount) / obj.total_installments, 2)
        return float(obj.amount)

    def create(self, validated_data):
        honorario = Honorario.objects.create(**validated_data)
        self._generate_installments(honorario)
        return honorario

    def update(self, instance, validated_data):
        amount_changed = "amount" in validated_data and validated_data["amount"] != instance.amount
        installments_changed = "total_installments" in validated_data and validated_data["total_installments"] != instance.total_installments
        date_changed = "date" in validated_data and validated_data["date"] != instance.date

        instance = super().update(instance, validated_data)

        if amount_changed or installments_changed or date_changed:
            instance.installments.all().delete()
            self._generate_installments(instance)
            
        return instance

    def _generate_installments(self, honorario):
        total_amount = honorario.amount
        installments_count = honorario.total_installments if honorario.is_installment else 1
        
        base_amount = (total_amount / installments_count).quantize(Decimal("0.01"))
        diff = total_amount - (base_amount * installments_count)

        for i in range(1, installments_count + 1):
            installment_amount = base_amount
            if i == installments_count:
                installment_amount += diff 
                
            ParcelaHonorario.objects.create(
                honorario=honorario,
                installment_number=i,
                amount=installment_amount,
                due_date=honorario.date + relativedelta(months=i-1),
                status=honorario.status
            )