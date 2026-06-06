from django.db import models
from django.conf import settings

class NotificationSetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="notification_settings"
    )
    
    enable_due_alerts = models.BooleanField(default=True)
    days_advance_taxes = models.PositiveIntegerField(default=5, help_text="Advance notice for taxes (days)")
    days_advance_rent = models.PositiveIntegerField(default=3, help_text="Advance notice for rent (days)")
    days_advance_others = models.PositiveIntegerField(default=1, help_text="Advance notice for other items (days)")
    
    enable_approval_requests = models.BooleanField(default=True)
    
    enable_weekly_summary = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification Settings - {self.user.email}"