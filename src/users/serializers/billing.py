from rest_framework import serializers
from ..models.billing import Subscription, Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "price", "interval"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source="plan", read_only=True)
    next_renewal = serializers.DateTimeField(source="current_period_end", format="%d/%m/%Y", read_only=True)
    is_premium_active = serializers.BooleanField(source="is_valid", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "status",
            "cancel_at_period_end",
            "next_renewal",
            "is_premium_active",
            "plan_details",
            "gateway_customer_id",
        ]
        read_only_fields = fields