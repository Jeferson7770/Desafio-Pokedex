import datetime
from django.utils import timezone
from rest_framework import serializers
from ..models.firm_member import FirmMember
from ..models.firm_structure import Firm
from ..models.subscription import FirmSubscription

TRIAL_DAYS = 7


class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = ["id", "name", "type", "created_at"]


class FirmCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = ["id", "name", "type"]

    def create(self, validated_data):
        user = self.context["request"].user

        firm = Firm.objects.create(**validated_data)

        FirmMember.objects.create(
            firm=firm,
            user=user,
            role=FirmMember.Role.OWNER,
        )

        FirmSubscription.objects.create(
            firm=firm,
            status=FirmSubscription.SubscriptionStatus.TRIAL,
            trial_ends_at=timezone.now() + datetime.timedelta(days=TRIAL_DAYS),
        )

        return firm


class FirmMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FirmMember
        fields = ["id", "user", "user_email", "role", "created_at"]