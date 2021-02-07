from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint, Count, F

from apps.core.models import TimeStampModel
from apps.user.models import User


def get_path(instance, filename):
    ext = filename.split('.')[-1]
    name = str(uuid4())

    return f"images/{name}.{ext}"


class Image(models.Model):
    image = models.ImageField(upload_to=get_path)


class ChannelManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(subscribers_count=Count(F('subscribers__id'), distinct=True))


class Channel(TimeStampModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_private = models.BooleanField(default=False)
    is_official = models.BooleanField(default=False)

    image = models.OneToOneField(Image, on_delete=models.SET_NULL, null=True)

    subscribers = models.ManyToManyField(
        User,
        through='UserChannel',
        through_fields=('channel', 'user'),
        blank=True
    )

    objects = ChannelManager()


class UserChannel(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    is_manager = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('channel', 'user'),
                name='subscribe_should_be_unique'
            )
        ]
