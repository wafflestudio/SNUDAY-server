from rest_framework import serializers

from apps.notice.models import Notice, NoticeImage
from apps.user.models import User
from apps.channel.models import Channel
from apps.channel.serializers import ChannelSerializer


class NoticeSerializer(serializers.ModelSerializer):
    images = serializers.ImageField(required=False)

    class Meta:
        model = Notice
        fields = (
            'id',
            'title',
            'contents',
            'channel',
            'writer',
            'created_at',
            'updated_at',
            'images',
        )



    