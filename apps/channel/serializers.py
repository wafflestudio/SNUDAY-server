from django.forms import ValidationError
from rest_framework import serializers
from apps.channel.models import Channel, Image

# TODO: S3 연결 후 이미지 처리하기
from apps.user.models import User
from apps.user.serializers import UserSerializer


class ChannelSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField(read_only=True)
    # managers_id = serializers.ListField(
    #     child=serializers.CharField(), write_only=True, required=False
    # )
    managers_id = serializers.CharField(
        write_only=True, required=False, allow_null=True
    )
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
        return UserSerializer(channel.managers, context=self.context).data

    def get_image(self, channel):
        if Image.objects.filter(channel=channel).exists():
            path = Image.objects.filter(id=channel.image_id).first().image.url
        else:
            path = None
        return path

    def get_subscribers_count(self, channel):
        subscribers_count = channel.subscribers.count()
        return subscribers_count

    def validate(self, data):

        if "managers_id" in data and data["managers_id"]:
            try:
                q = User.objects.get(username=data["managers_id"])

                data["managers_id"] = q.id
            except User.DoesNotExist:
                raise serializers.ValidationError("존재하지 않는 사용자를 관리자로 지정하였습니다.")

        return data


class ChannelAwaiterSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField(read_only=True)
    # managers_id = serializers.ListField(
    #     child=serializers.CharField(), write_only=True, required=False
    # )
    managers_id = serializers.CharField(write_only=True)
    managers = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(required=False)
    awaiters_count = serializers.SerializerMethodField(read_only=True)

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
        return UserSerializer(channel.managers, context=self.context).data

    def get_awaiters_count(self, channel):
        awaiters_count = channel.awaiters.count()
        return awaiters_count

    def get_image(self, channel):
        if Image.objects.filter(channel=channel).exists():
            path = Image.objects.filter(id=channel.image_id).first().image.url
        else:
            path = None
        return path

    def get_subscribers_count(self, channel):
        subscribers_count = channel.subscribers.count()
        return subscribers_count

    def validate(self, data):
        if "managers_id" in data:
            username = data.pop("managers_id", None)

            if not username:
                raise serializers.ValidationError("매니저가 있어야 합니다.")

            data["managers"] = User.objects.filter(username__in=username)

        return data
