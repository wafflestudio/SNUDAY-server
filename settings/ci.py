from .base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "mysql",
        "USER": "mysql",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "3306",
    },
}