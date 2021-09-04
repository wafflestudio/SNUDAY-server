from rest_framework import serializers
from apps.channel.models import Channel, Image

# TODO: S3 연결 후 이미지 처리하기
from apps.user.models import User
from apps.user.serializers import UserSerializer


class ChannelSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.IntegerField(read_only=True)
    # managers_id = serializers.ListField(
    #     child=serializers.CharField(), write_only=True, required=False
    # )
    managers_id = serializers.CharField(write_only=True, required=False)
    managers = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(required=False)

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
        return UserSerializer(
            channel.managers.all(), many=True, context=self.context
        ).data

    def get_image(self, channel):
        if Image.objects.filter(channel=channel).exists():
            path = Image.objects.filter(id=channel.image_id).first().image.url
        else:
            path = None
        return path

    def validate(self, data):
        if "managers_id" in data:
            usernames = data.pop("managers_id", [])

            if not usernames:
                raise serializers.ValidationError("매니저가 있어야 합니다.")

            data["managers"] = User.objects.filter(username__in=usernames)

        return data


class ChannelAwaiterSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.IntegerField(read_only=True)
    # managers_id = serializers.ListField(
    #     child=serializers.CharField(), write_only=True, required=False
    # )
    managers_id = serializers.CharField(write_only=True, required=True)
    managers = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    awaiters_count = serializers.SerializerMethodField()

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
            "awaiters_count",
            "managers",
            "managers_id",
        )

    def get_managers(self, channel):
        return UserSerializer(channel.managers, many=True, context=self.context).data

    def get_awaiters_count(self, channel):
        awaiters_count = channel.awaiters.count()
        return awaiters_count

    def validate(self, data):
        if "managers_id" in data:
            usernames = data.pop("managers_id", [])

            if not usernames:
                raise serializers.ValidationError("매니저가 있어야 합니다.")

            data["managers"] = User.objects.filter(username__in=usernames)

        return data
