from rest_framework import serializers

from apps.notice.models import Notice, NoticeImage
from apps.user.models import User
from apps.channel.models import Channel


class NoticeSerializer(serializers.ModelSerializer):
    images = serializers.ImageField(required=False)

    class Meta:
        model = Notice
        fields = (
            "id",
            "title",
            "contents",
            "channel",
            "writer",
            "created_at",
            "updated_at",
            "images",
        )


# serializer for notice data with CHANNEL NAME
class NoticeChannelNameSerializer(serializers.ModelSerializer):
    channel_name = serializers.SerializerMethodField()
    images = serializers.ImageField(required=False)

    class Meta:
        model = Notice
        fields = (
            "id",
            "title",
            "contents",
            "channel",
            "channel_name",
            "writer",
            "created_at",
            "updated_at",
            "images",
        )

    def get_channel_name(self, notice):
        return notice.channel.name
