from django.db import models

from apps.user.models import User
from apps.core.models import TimeStampModel
from apps.channel.models import Image, Channel


class Notice(TimeStampModel):
    title = models.CharField(max_length=100)
    contents = models.TextField()
    writer = models.ForeignKey(
        User,
        related_name="writer",
        on_delete=models.SET_NULL,
        db_column="writer_id",
        null=True,
    )
    channel = models.ForeignKey(
        Channel,
        related_name="channel",
        on_delete=models.CASCADE,
        db_column="channel_id",
    )


class NoticeImage(Image):
    notice = models.ForeignKey(
        Notice, related_name="notice", on_delete=models.CASCADE, db_column="notice_id"
    )
