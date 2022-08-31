from django.forms import ValidationError
from rest_framework import serializers
from apps.channel.models import Channel, Image, UserChannel
from apps.core.utils import THEME_COLOR, random_color

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
    color = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = (
            "id",
            "name",
            "image",
            "color",
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

    def get_color(self, channel):
        if "request" not in self.context:
            return None
        request = self.context["request"]
        if request is None or not request.user.is_authenticated:
            return None
        try:
            color = UserChannel.objects.get(channel=channel, user=request.user).color
        except UserChannel.DoesNotExist:
            return None
        return color

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
    color = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = (
            "id",
            "name",
            "image",
            "color",
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

    def get_color(self, channel):
        if "request" not in self.context:
            return random_color()
        request = self.context["request"]
        if request is None:
            return random_color()
        try:
            color_data = UserChannelColorSerializer(
                UserChannel.objects.get(channel=channel, user=request.user),
                context={"request": request},
            )
        except UserChannel.DoesNotExist:
            return random_color()
        return color_data.data["color"]

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


class UserChannelColorSerializer(serializers.ModelSerializer):

    channel = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserChannel
        fields = ("channel", "user", "color")

    def get_channel(self, obj):
        return ChannelSerializer(obj.channel, context=self.context).data

    def get_user(self, obj):
        return UserSerializer(obj.user, context=self.context).data

    def validate(self, data):
        if "color" not in data or data["color"] is None:
            data["color"] = random_color()
        if data.get("color") not in THEME_COLOR.values():
            raise serializers.ValidationError("테마에 없는 색입니다.")
        return data
