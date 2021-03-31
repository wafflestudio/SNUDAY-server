from django.db import models

from apps.user.models import User
from apps.core.models import TimeStampModel
from apps.channel.models import Channel


class Event(TimeStampModel):
    title = models.CharField(max_length=100)
    memo = models.TextField(null=True)
    writer = models.ForeignKey(
        User,
        related_name="event_writer",
        on_delete=models.SET_NULL,
        db_column="writer_id",
        null=True,
    )
    channel = models.ForeignKey(
        Channel,
        related_name="event_channel",
        on_delete=models.CASCADE,
        db_column="channel_id",
    )
    has_time = models.BooleanField()
    start_date = models.DateField(blank=True)
    due_date = models.DateField(blank=True)

    start_time = models.TimeField(null=True)
    due_time = models.TimeField(null=True)
