from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models.case_payment import CasePaymentSchedule
from ..models.case_structure import Client, Process


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "firm",
            "name",
            "email",
            "phone",
            "cpf_cnpj",
            "type",
            "notes",
            "created_at",
        ]
        read_only_fields = ["firm"]


class CasePaymentScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CasePaymentSchedule
        fields = ["id", "amount", "expected_date", "probability", "paid"]


class ProcessSerializer(serializers.ModelSerializer):
    schedules = CasePaymentScheduleSerializer(many=True, required=False)
    client_details = ClientSerializer(source="client", read_only=True)

    class Meta:
        model = Process
        fields = [
            "id",
            "firm",
            "client",
            "client_details",
            "client_name",
            "title",
            "status",
            "total_fee",
            "payment_type",
            "win_probability",
            "stage",
            "expected_close_date",
            "schedules",
            "created_at",
        ]
        read_only_fields = ["firm"]

    def create(self, validated_data):
        schedules_data = validated_data.pop("schedules", [])
        membership = self.context["request"].user.firm_memberships.first()
        if not membership:
            raise ValidationError("O usuario nao possui nenhuma empresa vinculada.")
        firm = membership.firm

        client = validated_data.get("client")
        if client:
            validated_data["client_name"] = client.name

        process = Process.objects.create(firm=firm, **validated_data)

        for schedule in schedules_data:
            CasePaymentSchedule.objects.create(case=process, **schedule)

        return process

    def update(self, instance, validated_data):
        client = validated_data.get("client")
        if client:
            validated_data["client_name"] = client.name
        return super().update(instance, validated_data)


class CaseSerializer(ProcessSerializer):
    pass