import os
import posthog
from decouple import config
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "src.users"

    def ready(self):
        api_key = config("POSTHOG_API_KEY", default=None)
        host = config("POSTHOG_HOST", default="https://us.i.posthog.com")

        if api_key:
            posthog.api_key = api_key
            posthog.host = host
        else:
            posthog.disabled = True