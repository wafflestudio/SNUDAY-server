from django.db import models

from apps.user.models import User
from apps.core.models import TimeStampModel
from apps.channel.models import Channel

class Event(TimeStampModel):
    contents = models.CharField(max_length=100)
    writer = models.ForeignKey(User, related_name="event_writer", on_delete=models.SET_NULL, db_column="writer_id", null=True)
    channel = models.ForeignKey(Channel, related_name="event_channel", on_delete=models.CASCADE, db_column="channel_id")
    has_time = models.BooleanField()
    start_date = models.DateTimeField(null = True)
    due_date = models.DateTimeField(null = True)