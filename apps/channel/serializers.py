from rest_framework import serializers

from apps.channel.models import Channel


# TODO: S3 연결 후 이미지 처리하기
class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = (
            'name',
            'description',
            'is_private',
            'is_official',
            'created_at',
            'updated_at',
        )