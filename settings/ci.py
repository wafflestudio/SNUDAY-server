from .base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "github-actions",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    },
}