from random import choices
from string import ascii_uppercase, digits


def is_verified_email(email_prefix):
    from apps.user.models import EmailInfo

    return EmailInfo.objects.filter(
        email_prefix=email_prefix, is_verified=True
    ).exists()


def random_string(size):
    return "".join(choices(ascii_uppercase + digits, k=size))
