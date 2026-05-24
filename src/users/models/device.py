from django.db import models
from django.conf import settings

class UserDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=255)
    browser = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_login = models.DateTimeField(auto_now=True)
    refresh_token_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["-last_login"]

    def __str__(self):
        return f"{self.device_name} ({self.user.email})"