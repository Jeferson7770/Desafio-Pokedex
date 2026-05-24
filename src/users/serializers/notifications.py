from rest_framework import serializers
from ..models.notifications import NotificationSetting

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = [
            "id",
            "enable_due_alerts",
            "days_advance_taxes",
            "days_advance_rent",
            "days_advance_others",
            "enable_approval_requests",
            "enable_weekly_summary",
        ]