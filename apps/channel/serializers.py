from rest_framework import serializers

from apps.channel.models import Channel
# TODO: S3 연결 후 이미지 처리하기
from apps.user.serializers import UserSerializer


class ChannelSerializer(serializers.ModelSerializer):
    managers = serializers.SerializerMethodField()
    subscribers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Channel
        fields = (
            'name',
            'description',
            'is_private',
            'is_official',
            'created_at',
            'updated_at',
            'subscribers_count',
            'managers',
        )

    def get_managers(self, channel):
        return UserSerializer(channel.managers, many=True, context=self.context).data
