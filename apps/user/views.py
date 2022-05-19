from django.core.mail import EmailMessage
from django.db.models import Q
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from string import ascii_letters, digits, punctuation
import secrets

from apps.channel.serializers import ChannelSerializer, ChannelAwaiterSerializer
from apps.core.mixins import SerializerChoiceMixin
from apps.user.models import User, EmailInfo
from apps.user.serializers import UserSerializer, UserPasswordSerializer


class UserViewSet(
    SerializerChoiceMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_classes = {
        "default": UserSerializer,
        "subscribing_channels": ChannelSerializer,
        "managing_channels": ChannelAwaiterSerializer,
        "awaiting_channels": ChannelSerializer,
        "change_password": UserPasswordSerializer,
    }

    def get_permissions(self):
        if self.action in (
            "create",
            "login",
            "verify_email",
            "refresh",
            "find_password",
            "find_username",
        ):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, user_pk=None):
        """
        # 나의 정보 얻기
        """
        user = (
            request.user
            if user_pk == "me"
            else self.queryset.get(pk=self.request.user.id)
        )
        return Response(self.get_serializer(user).data)

    def update(self, request, user_pk=None):
        """
        # 업데이트하기
        * 다른 이의 정보를 업데이트 할 수 없음
        """
        if user_pk != "me":
            return Response(
                "다른 사람의 정보를 업데이트 할 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )

        user = request.user
        data = request.data.copy()

        if "password" in data:
            return Response("패스워드를 업데이트 할 수 없습니다.", status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def subscribing_channels(self, request, user_pk=None):
        """
        # 구독 중인 채널
        """
        if user_pk != "me":
            return Response(
                "다른 이가 구독중인 채널을 볼 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )
        qs = request.user.subscribing_channels.filter(is_personal=False)
        data = self.get_serializer(qs, many=True).data
        return Response(data)

    @action(detail=True, methods=["GET"])
    def managing_channels(self, request, user_pk=None):
        """
        # 관리 중인 채널
        """
        if user_pk != "me":
            return Response(
                "다른 이가 관리중인 채널을 볼 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )
        qs = request.user.managing_channels.filter(is_personal=False)
        data = self.get_serializer(qs, many=True).data
        return Response(data)

    @action(detail=True, methods=["GET"])
    def awaiting_channels(self, request, user_pk=None):
        """
        # 구독 신청 후 대기 중인 private 채널
        """
        if user_pk != "me":
            return Response(
                "다른 이가 대기중인 채널을 볼 수 없습니다.", status=status.HTTP_403_FORBIDDEN
            )
        qs = request.user.awaiting_channels.all()
        data = self.get_serializer(qs, many=True).data
        return Response(data)

    @action(detail=True, methods=["PATCH"])
    def change_password(self, request, user_pk=None):
        """
        비밀번호 변경하기
        """

        if user_pk != "me":
            return Response("다른 사람의 비밀번호를 바꿀 수 없습니다.", status=status.HTTP_403_FORBIDDEN)

        user = request.user
        data = request.data.copy()

        serializer = self.get_serializer(data=data, partial=True)

        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if serializer.data.get("old_password") == serializer.data.get(
                "new_password"
            ):
                return Response(
                    "기존 비밀번호와 새 비밀번호가 같습니다.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.data.get("new_password"))
            user.save()

            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Password updated successfully",
                "data": [],
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def search(self, request):
        """
        # username 검색 API
        * params의 'type'으로 검색 타입 'username'
        * params의 'q'로 검색어를 받음
        """
        qs = User.objects.all()
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(param["q"]) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        if search_keyword:
            if search_type == "username":
                qs = qs.filter(Q(username__icontains=search_keyword))[:5]

            if not qs.exists():
                return Response(
                    {"error": "검색 결과가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
                )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        # user 생성 api
        * username이 admin인 사용자의 채널을 자동으로 구독하도록 설정
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            admin = User.objects.get(username="admin")
            for channel in admin.managing_channels.all():
                channel.subscribers.add(user)
        except User.DoesNotExist:  # admin이 없는 경우(테스트 상황에서 그럴 수 있음)
            pass
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def send_email(request):
    """
    # 이메일 발송하기
    * request의 `body`로 `email_prefix`를 주어야함
    """
    email_prefix = request.data.get("email_prefix")

    try:
        info = EmailInfo.objects.get(email_prefix=email_prefix)
        if info.is_verified == True:
            return Response("이미 인증된 회원입니다.", status=status.HTTP_400_BAD_REQUEST)
    except EmailInfo.DoesNotExist:
        pass

    EmailInfo.objects.filter(email_prefix=email_prefix).delete()
    info = EmailInfo.of(email_prefix)

    email = EmailMessage(
        "SNUDAY 이메일 인증", info.verification_code, to=[f"{email_prefix}@snu.ac.kr"]
    )

    email.send()

    return Response("인증코드가 발송되었습니다.")


@api_view(["POST"])
def find_username(request):
    """
    # 아이디 찾기
    * request의 `body`로 `email_prefix`를 주어야함
    * 해당 메일로 가입된 아이디를 메일로 발송함.
    """
    email_prefix = request.data.get("email_prefix")

    email_info = EmailInfo.objects.filter(email_prefix=email_prefix).first()

    if email_info is not None:
        user = User.objects.get(email=f"{email_prefix}@snu.ac.kr")
        email = EmailMessage(
            "SNUDAY 아이디 찾기", user.username, to=[f"{email_prefix}@snu.ac.kr"]
        )
        email.send()

    else:
        return Response("해당 메일로 가입된 회원이 없습니다.", status=status.HTTP_400_BAD_REQUEST)

    return Response("메일로 아이디가 발송되었습니다.")


@api_view(["POST"])
def find_password(request):
    """
    # 비밀번호 임시 발급
    * request의 `body`로 `email_prefix`를 주어야함
    * 입력한 메일로 가입된 계정의 임시 비밀번호를 메일로 발송함.
    """
    email_prefix = request.data.get("email_prefix")
    q_username = request.data.get("username")
    q_first_name = request.data.get("first_name")
    q_last_name = request.data.get("last_name")

    email_info = EmailInfo.objects.filter(email_prefix=email_prefix).first()

    if email_info is not None:
        user = User.objects.get(email=f"{email_prefix}@snu.ac.kr")

        username_check = q_username == user.username
        first_name_check = q_first_name == user.first_name
        last_name_check = q_last_name == user.last_name

        if not username_check or not first_name_check or not last_name_check:
            return Response(
                "입력하신 정보와 일치하는 회원이 없습니다", status=status.HTTP_400_BAD_REQUEST
            )

        temp_password = new_password()

        user.set_password(temp_password)
        user.save()

        email = EmailMessage(
            "SNUDAY 비밀번호 재발급", temp_password, to=[f"{email_prefix}@snu.ac.kr"]
        )
        email.send()

    else:
        return Response("해당 메일로 가입된 회원이 없습니다.", status=status.HTTP_400_BAD_REQUEST)

    return Response("메일로 새로 발급된 비밀번호가 발송되었습니다.")


def new_password():
    string_pool = ascii_letters + digits + punctuation

    while True:
        temp_password = "".join(secrets.choice(string_pool) for i in range(10))
        if (
            any(c.islower() for c in temp_password)
            and any(c.isupper() for c in temp_password)
            and sum(c.isdigit() for c in temp_password) >= 2
        ):
            break

    return temp_password


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
