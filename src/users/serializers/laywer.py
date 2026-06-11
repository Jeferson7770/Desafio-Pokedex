from rest_framework import serializers
from django.utils import timezone
from ..models.laywer import LawyerProfile
from ..models.device import UserDevice
from ...finance.models.dinheiro import BankAccount

from .notifications import NotificationSettingSerializer

class OfficeProfileSerializer(serializers.Serializer):
    office_name = serializers.SerializerMethodField()
    cnpj_or_cpf = serializers.CharField(source="cpf")
    contact_email = serializers.SerializerMethodField()
    tax_regime_display = serializers.CharField(source="get_tax_regime_display", read_only=True)
    tax_regime = serializers.CharField()

    def get_office_name(self, obj) -> str:
        if "office_name" in self.context:
            return self.context["office_name"]
        membership = obj.user.firm_memberships.select_related('firm').first()
        return membership.firm.name if membership else ""

    def get_contact_email(self, obj) -> str:
        return obj.user.email


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ["id", "device_name", "browser", "ip_address", "last_login"]


class LawyerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    devices = UserDeviceSerializer(source="user.devices", many=True, read_only=True)
    billing = serializers.SerializerMethodField()
    notifications = NotificationSettingSerializer(source="user.notification_settings", read_only=True, allow_null=True)
    
    has_bank_connected = serializers.SerializerMethodField()
    office_profile = serializers.SerializerMethodField()

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
            "is_active",
            "devices",
            "billing",
            "notifications",
            "office_profile",
            "created_at",
        ]
        read_only_fields = ["created_at", "has_bank_connected", "email", "devices", "billing", "notifications", "office_profile"]

    def _get_membership(self, obj):
        """Single DB query shared by all SerializerMethodFields that need firm data."""
        if not hasattr(obj, "_cached_membership"):
            obj._cached_membership = (
                obj.user.firm_memberships
                .select_related("firm__subscription__plan")
                .first()
            )
        return obj._cached_membership

    def get_has_bank_connected(self, obj) -> bool:
        membership = self._get_membership(obj)
        if not membership:
            return False
        return BankAccount.objects.filter(
            firm_id=membership.firm_id,
            external_account_id__isnull=False
        ).exists()

    def get_billing(self, obj):
        try:
            membership = self._get_membership(obj)
            if not membership:
                return None
            sub = getattr(membership.firm, 'subscription', None)
            if not sub:
                return None
            is_active = sub.status == 'ACTIVE' and (
                sub.current_period_end is None or sub.current_period_end > timezone.now()
            )
            return {
                "status": sub.status,
                "is_premium_active": is_active,
                "next_renewal": (
                    sub.current_period_end.strftime("%d/%m/%Y")
                    if sub.current_period_end else None
                ),
                "plan_details": {
                    "id": sub.plan.id,
                    "name": sub.plan.name,
                    "price": str(sub.plan.price),
                    "cycle": sub.plan.cycle,
                } if sub.plan_id else None,
            }
        except Exception:
            return None

    def get_office_profile(self, obj):
        membership = self._get_membership(obj)
        office_name = membership.firm.name if membership else ""
        return OfficeProfileSerializer(
            obj, context={"office_name": office_name}
        ).data

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