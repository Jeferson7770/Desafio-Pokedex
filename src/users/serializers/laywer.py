from rest_framework import serializers
from ..models.laywer import LawyerProfile
from ..models.device import UserDevice

from .billing import SubscriptionSerializer 
from .notifications import NotificationSettingSerializer


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ["id", "device_name", "browser", "ip_address", "last_login"]


class LawyerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    devices = UserDeviceSerializer(source="user.devices", many=True, read_only=True)
    billing = SubscriptionSerializer(source="user.subscription", read_only=True, allow_null=True)
    
    notifications = NotificationSettingSerializer(source="user.notification_settings", read_only=True, allow_null=True)

    class Meta:
        model = LawyerProfile
        fields = [
            "email",
            "full_name",
            "phone",
            "oab_number",
            "oab_state",
            "cpf",
            "birth_date",
            "years_of_experience",
            "tax_regime",
            "cep",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "office_type",
            "practice_areas",
            "has_employees",
            "average_monthly_income",
            "average_monthly_expense",
            "income_variability",
            "has_bank_connected",
            "goal_type",
            "financial_goal",
            "onboarding_completed",
            "devices",
            "billing",
            "notifications",
            "created_at",
        ]
        read_only_fields = ["created_at", "has_bank_connected", "email", "devices", "billing", "notifications"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            if hasattr(request.user, "profile"):
                raise serializers.ValidationError(
                    {"detail": "Este usuário já possui um perfil de advogado cadastrado."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)