from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.user.utils import random_string


class User(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, verbose_name="email address", unique=True)


class EmailInfo(models.Model):
    email_prefix = models.CharField(max_length=100, unique=True)
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)

    @staticmethod
    def of(email_prefix):
        return EmailInfo.objects.create(
            email_prefix=email_prefix, verification_code=random_string(6)
        )

    @staticmethod
    def of(email_prefix, is_verified):
        return EmailInfo.objects.create(
            email_prefix=email_prefix,
            verification_code=random_string(6),
            is_verified=is_verified,
        )
