from rest_framework import serializers
from apps.channel.models import Channel

# TODO: S3 연결 후 이미지 처리하기
from apps.user.models import User
from apps.user.serializers import UserSerializer


class ChannelSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.IntegerField(read_only=True)
    managers_id = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    managers = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = (
            "id",
            "name",
            "image",
            "description",
            "is_private",
            "is_official",
            "is_personal",
            "created_at",
            "updated_at",
            "subscribers_count",
            "managers",
            "managers_id",
        )

    def get_managers(self, channel):
        return UserSerializer(channel.managers, many=True, context=self.context).data

    def validate(self, data):
        if "managers_id" in data:
            ids = data.pop("managers_id", [])

            if not ids:
                raise serializers.ValidationError("매니저가 있어야 합니다.")

            data["managers"] = User.objects.filter(id__in=ids)

        return data
