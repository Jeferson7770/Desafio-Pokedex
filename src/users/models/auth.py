from django.contrib.auth.models import AbstractUser
from django.db import models
from ..models.manager import UserManager

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email