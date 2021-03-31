from django.core.mail import EmailMessage
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.channel.serializers import ChannelSerializer
from apps.core.mixins import SerializerChoiceMixin
from apps.user.models import User, EmailInfo
from apps.user.serializers import UserSerializer
from apps.user.utils import is_verified_email


class UserViewSet(
    SerializerChoiceMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_classes = {
        "default": UserSerializer,
        "subscribing_channels": ChannelSerializer,
        "managing_channels": ChannelSerializer,
    }

    def get_permissions(self):
        if self.action in ("create", "login", "verify_email", "refresh"):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, pk=None):
        """
        # 나의 정보 얻기
        """
        user = request.user if pk == "me" else self.get_object()
        return Response(self.get_serializer(user).data)

    def update(self, request, pk=None):
        """
        # 업데이트하기
        * 다른 이의 정보를 업데이트 할 수 없음
        """
        if pk != "me":
            return Response(
                "다른 사람의 정보를 업데이트 할 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )

        user = request.user
        data = request.data.copy()

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def subscribing_channels(self, request, pk=None):
        """
        # 구독 중인 채널
        """
        if pk != "me":
            return Response(
                "다른 이가 구독중인 채널을 볼 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )
        qs = request.user.subscribing_channels.all()
        page = self.paginate_queryset(qs)
        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)

    @action(detail=True, methods=["GET"])
    def managing_channels(self, request, pk=None):
        """
        # 관리 중인 채널
        """
        if pk != "me":
            return Response(
                "다른 이가 관리중인 채널을 볼 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )
        qs = request.user.managing_channels.all()
        page = self.paginate_queryset(qs)
        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)


@api_view(["POST"])
def send_email(request):
    """
    # 이메일 발송하
    * request의 `body`로 `email_prefix`를 주어야함
    """
    email_prefix = request.data.get("email_prefix")

    EmailInfo.objects.filter(email_prefix=email_prefix).delete()
    info = EmailInfo.of(email_prefix)

    email = EmailMessage(
        "SNUDAY 이메일 인증", info.verification_code, to=[f"{email_prefix}@snu.ac.kr"]
    )

    return Response("인증코드가 발송되었습니다.")


@api_view(["POST"])
def verify_email(request):
    """
    # 이메일 인증하기
    * request의 `body`로 `email_prefix`와 6자리 코드(`code`)를 주어야함
    """
    email_prefix = request.data.get("email_prefix")
    code = request.data.get("code")

    try:
        info = EmailInfo.objects.get(email_prefix=email_prefix)
    except EmailInfo.DoesNotExist:
        return Response("해당하는 이메일 정보가 없습니다.", status=status.HTTP_400_BAD_REQUEST)

    if info.verification_code != code:
        return Response("잘못된 인증 코드입니다.", status=status.HTTP_400_BAD_REQUEST)

    info.is_verified = True
    info.save()

    return Response("이메일 인증에 성공했습니다.")
