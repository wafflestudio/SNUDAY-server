from django.db import transaction
from rest_framework import serializers

from apps.channel.models import Channel, ManagerChannel
from apps.user.models import User
from apps.user.utils import is_verified_email


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("중복된 이메일입니다.")

        if not is_verified_email(value[: value.find("@")]):
            raise serializers.ValidationError("인증되지 않은 이메일입니다.")

        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("중복된 아이디입니다.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        u = User.objects.create_user(**validated_data)
        c = Channel.objects.create(
            name=f"{u.username}의 채널",
            description="개인 채널입니다.",
            is_private=True,
            is_personal=True,
        )
        ManagerChannel.objects.create(user=u, channel=c)
        return u


class UserPasswordSerializer(serializers.Serializer):
    model = User

    """
    Serializer for password change endpoint.
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
