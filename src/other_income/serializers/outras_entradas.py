from decimal import Decimal
from dateutil.relativedelta import relativedelta
from rest_framework import serializers

from ..models.outras_entradas import OutraEntrada, OutraEntradaInstallment


class OutraEntradaInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutraEntradaInstallment
        fields = [
            "id",
            "installment_number",
            "amount",
            "due_date",
            "status",
            "late_interest_cost",
            "paid_at",
        ]
        read_only_fields = ["id", "installment_number", "amount", "due_date", "late_interest_cost"]


class OutraEntradaSerializer(serializers.ModelSerializer):
    installments = OutraEntradaInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = OutraEntrada
        fields = [
            "id",
            "firm",
            "title",
            "amount",
            "date",
            "status",
            "notes",
            "created_at",
            "is_installment",
            "total_installments",
            "installment_value",
            "interest_rate_month",
            "installments",
        ]
        read_only_fields = ["id", "firm", "created_at"]

    def validate(self, attrs):
        is_installment = attrs.get("is_installment", getattr(self.instance, "is_installment", False))
        total_installments = attrs.get("total_installments", getattr(self.instance, "total_installments", 1))
        installment_value = attrs.get("installment_value", getattr(self.instance, "installment_value", None))
        amount = attrs.get("amount", getattr(self.instance, "amount", None))

        if total_installments < 1:
            raise serializers.ValidationError({"total_installments": "Deve ser maior ou igual a 1."})

        if installment_value is None:
            raise serializers.ValidationError({"installment_value": "Este campo é obrigatório."})

        if is_installment and total_installments == 1:
            raise serializers.ValidationError(
                {"total_installments": "Para entradas parceladas, informe total_installments maior que 1."}
            )

        if not is_installment and total_installments != 1:
            raise serializers.ValidationError(
                {"total_installments": "Para entradas sem parcelamento, total_installments deve ser 1."}
            )

        if amount is not None:
            if is_installment:
                expected_total = (installment_value * total_installments).quantize(Decimal("0.01"))
                if amount != expected_total:
                    raise serializers.ValidationError(
                        {
                            "amount": "Para entradas parceladas, amount deve ser igual a installment_value * total_installments."
                        }
                    )
            elif amount != installment_value:
                raise serializers.ValidationError(
                    {"installment_value": "Para entradas sem parcelamento, installment_value deve ser igual a amount."}
                )

        return attrs

    def create(self, validated_data):
        if validated_data.get("is_installment"):
            validated_data["status"] = OutraEntrada.Status.PENDENTE

        outra_entrada = OutraEntrada.objects.create(**validated_data)

        if outra_entrada.is_installment:
            self._generate_installments(outra_entrada)

        return outra_entrada

    def update(self, instance, validated_data):
        is_now_installment = validated_data.get("is_installment", instance.is_installment)
        converting_to_installment = not instance.is_installment and is_now_installment

        if instance.is_installment and "status" in validated_data:
            raise serializers.ValidationError(
                {"status": "Para entradas parceladas, atualize o status por parcela."}
            )

        new_status = validated_data.get("status")
        status_changed = new_status is not None and new_status != instance.status

        if converting_to_installment:
            validated_data["status"] = OutraEntrada.Status.PENDENTE

        structure_changed = instance.is_installment and any(
            key in validated_data for key in ["total_installments", "installment_value", "date", "amount"]
        )

        instance = super().update(instance, validated_data)

        if converting_to_installment or structure_changed:
            instance.installments.all().delete()
            self._generate_installments(instance)
        elif status_changed and not instance.is_installment:
            instance.installments.all().update(status=new_status)

        return instance

    def _generate_installments(self, outra_entrada):
        for i in range(1, outra_entrada.total_installments + 1):
            OutraEntradaInstallment.objects.create(
                outra_entrada=outra_entrada,
                installment_number=i,
                amount=outra_entrada.installment_value,
                due_date=outra_entrada.date + relativedelta(months=i - 1),
                status=OutraEntradaInstallment.Status.PENDENTE,
            )
