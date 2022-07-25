from dataclasses import dataclass
from django.db.models import Q
from django.db import transaction
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.channel.exceptions import NoSubscriberInPrivateChannel

from apps.channel.models import Channel, Image, UserChannel
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer, UserChannelColorSerializer
from apps.core.utils import THEME_COLOR, random_color
from apps.user.models import User
from apps.user.serializers import UserSerializer
import re


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [ManagerCanModify]

    def create(self, request):
        """
                # 채널을 만드는 API
                * `managers_id`는 매니저의 `username`을 하나의 string으로 넣어야 함
                * image는 얻게 된 이미지        * `is_private`은 비공개채널 여부에 대한 를 첨부할 것
        설정
                * `is_personal`은 개인 채널인지 여부에 대한 설정
        """
        user = request.user
        data = request.data.copy()

        if "name" in data:
            q_channel = Channel.objects.filter(name=data["name"]).first()

            if q_channel is not None:
                return Response(
                    {"error": "동일한 이름의 채널이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST
                )

        if "managers_id" not in data:
            return Response(
                {"error": "managers_id에 manager의 username을 입력해야합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                channel = Channel.objects.get(id=serializer.data["id"])

                if "image" in data:
                    image = Image.objects.create(image=data["image"])
                    image.channel = channel
                    image.save()

                serializer = self.get_serializer(channel, data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                manager_obj = User.objects.get(
                    username=data["managers_id"]
                    if data["managers_id"]
                    else user.username
                )
                channel.managers = manager_obj
                channel.subscribers.add(manager_obj)
                channel.save()

                color_serializer = UserChannelColorSerializer(
                    UserChannel.objects.get(channel=channel, user=user),
                    data={"color": random_color()},
                    context={"request": request},
                    partial=True,
                )

                color_serializer.is_valid(raise_exception=True)
                color_serializer.save()

                if (
                    serializer.data["is_private"]
                    and serializer.data["subscribers_count"] == 0
                ):
                    raise NoSubscriberInPrivateChannel

        except NoSubscriberInPrivateChannel:
            return Response(
                {"error": "비공개 채널에 구독자가 한 명도 없어, 비공개 채널에 접근할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        """
        # 전체 채널 목록 API
        * personal channel을 제외한 모든 채널의 목록을 가져옴.
        * id의 역순으로.
        * pagination 적용됨.
        """
        qs = Channel.objects.filter(is_personal=False)
        page = self.paginate_queryset(qs)

        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)

    def partial_update(self, request, pk=None):
        """
        # 채널 수정 API
        * {id}에는 channel의 id를 넣으면 됨
        * 가급적 `PUT`보다 `PATCH`를 이용할 것
        * POST로 channel을 만드는 것과 동일
        * 매니저 수정 시에 자기 자신의 아이디가 제외되는 순간 매니저에서 제외되므로 주의할 것.
        """
        channel = self.get_object()
        data = request.data.copy()
        if "name" in data and channel.name != data["name"]:
            q_channel = Channel.objects.filter(name=data["name"]).first()

            if q_channel is not None:
                return Response(
                    {"error": "동일한 이름의 채널이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST
                )

        if "image" in data:
            image = Image.objects.create(image=data["image"], channel=channel)

        serializer = self.get_serializer(channel, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if "managers_id" in data and data["managers_id"]:
            current_manager = channel.managers
            if current_manager.id != data["managers_id"]:
                manager = User.objects.get(username=data["managers_id"])
                channel.managers = manager
                channel.subscribers.add(manager)

        serializer = self.get_serializer(channel, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        # 채널 삭제 API
        * {id}에는 channel의 id를 넣으면 됨
        * 해당 채널의 매니저만 가능
        * 존재하지 않는 채널이면 400
        * 해당 채널의 매니저가 아니면 403
        """
        try:
            channel_id = int(pk)
            channel = Channel.objects.filter(id=channel_id).first()

            if channel == None:
                return Response(
                    {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if channel.managers != request.user:
            return Response(
                {"error": "해당 채널의 매니저만 채널을 삭제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.check_object_permissions(self.request, channel)
        channel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, pk=None):
        """
        # 채널 정보 GET API
        * {id}에는 channel의 id를 넣으면 됨
        * private channel은 `400`
        """
        channel = self.get_object()
        if (
            channel.is_private
            and not channel.subscribers.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "private channel은 열람할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(channel)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def subscribe(self, request, pk):
        """
        # 구독
        * {channel_pk}에는 구독하려는 channel의 id를 넣으면 됨
        * 이미 구독중이라면 400
        * 비공개 채널이라면 대기자 명단에 올라감
        """
        channel = self.get_object()

        if channel.subscribers.filter(id=request.user.id).exists():
            return Response(
                {"error": "이미 구독 중입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        if channel.is_private:
            channel.awaiters.add(request.user)

        else:
            channel.subscribers.add(request.user)

            color_serializer = UserChannelColorSerializer(
                UserChannel.objects.get(channel=channel, user=request.user),
                data={
                    "channel": channel,
                    "user": request.user,
                    "color": random_color(),
                },
                context={"request": request},
            )
            color_serializer.is_valid(raise_exception=True)
            color_serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        """
        # 구독 취소
        * {channel_pk}에는 구독 취소하려는 channel의 id를 넣으면 됨
        * 구독 중이지 않다면 400
        """
        user = request.user
        channel = self.get_object()

        if (
            not channel.subscribers.filter(id=user.id).exists()
            and not channel.awaiters.filter(id=user.id).exists()
        ):
            return Response(
                {"error": "구독 중이 아닙니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        if channel.awaiters.filter(id=user.id).exists():
            channel.awaiters.remove(request.user)

        else:
            channel.subscribers.remove(request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def awaiters(self, request, pk):
        """
        # 대기자 명단
        * {id}에는 channel의 id를 넣으면 됨
        * 해당 (비공개)채널에 구독을 신청한 대기자들의 목록
        """
        channel = self.get_object()
        awaiters = channel.awaiters
        serializer = UserSerializer(awaiters, partial=True, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["post"], url_path="awaiters/allow/(?P<user_pk>[^/.]+)"
    )
    def allow(self, request, pk, user_pk):
        """
        # 매니저가 대기자들의 구독을 수락하는 API
        * {id}에는 channel의 id를 넣으면 됨
        * {user_pk}에는 user의 id를 넣으면 됨
        * 채널 매니저만 가능
        * 이미 구독중인 유저면 400
        * 구독 신청한 적이 없는 유저면 400
        """
        user = User.objects.get(id=user_pk)
        channel = self.get_object()

        if channel.subscribers.filter(id=user.id).exists():
            return Response(
                {"error": "해당 유저는 이미 구독 중입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        elif not channel.awaiters.filter(id=user.id).exists():
            return Response(
                {"error": "해당 유저는 구독 신청한 적이 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        else:
            channel.subscribers.add(user)
            channel.awaiters.remove(user)

            color_serializer = UserChannelColorSerializer(
                UserChannel.objects.get(channel=channel, user=user),
                data={"channel": channel, "user": user, "color": random_color()},
                context={"request": request},
            )
            color_serializer.is_valid(raise_exception=True)
            color_serializer.save()

        return Response(status=status.HTTP_200_OK)

    @allow.mapping.delete
    def disallow(self, request, pk, user_pk):
        """
        # 매니저가 대기자들의 구독을 거절하는 API
        * {id}에는 channel의 id를 넣으면 됨
        * {user_pk}에는 user의 id를 넣으면 됨
        * 채널 매니저만 가능
        * 이미 구독중인 유저면 400
        * 구독 신청한 적이 없는 유저면 400
        """
        channel = self.get_object()
        user = User.objects.get(id=user_pk)

        if channel.subscribers.filter(id=user.id).exists():
            return Response(
                {"error": "해당 유저는 이미 구독 중입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        elif not channel.awaiters.filter(id=user.id).exists():
            return Response(
                {"error": "해당 유저는 구독 신청한 적이 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        else:
            channel.awaiters.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def recommend(self, request):
        """
        # 채널 추천 API
        * 구독자가 가장 많은 5개의 채널들을 추천해줌.
        """
        channels = Channel.objects.filter(is_private=False, is_personal=False).order_by(
            "-subscribers_count"
        )[:5]
        serializer = self.get_serializer(channels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        # 채널 검색 API
        * params의 'type'으로 검색 타입 'all', 'name', 'description'을 받음
        * pararms의 'q'로 검색어를 받음
        """
        qs = Channel.objects.filter(is_personal=False)
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(param["q"]) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        if search_keyword:
            if search_type == "all":
                qs = qs.filter(
                    Q(name__icontains=search_keyword)
                    | Q(description__icontains=search_keyword)
                )
            elif search_type == "name":
                qs = qs.filter(Q(name__icontains=search_keyword))
            elif search_type == "description":
                qs = qs.filter(Q(description__icontains=search_keyword))

        page = self.paginate_queryset(qs)

        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)

    @action(detail=True, methods=["patch"])
    def color(self, request, pk):
        """
        # 색상 변경
        * {id}에는 색을 변경하려는 channel의 id를 넣으면 됨
        * 테마 색상에 없는 색을 입력 시 400
        * 그 채널을 구독한 상태가 아니면 400
        * 색상은 POMEGRANATE, ORANGE, YELLOW, LIGHTGREEN, GREEN, MEDITTERANEAN, SKYBLUE, AMETHYST, LAVENDER 중 하나로 입력
        * 각 채널에 지정한 색은 그 유저에게만 귀속됨, 타 유저에게는 영향을 미치지 않음
        """
        channel = self.get_object()
        if not channel.subscribers.filter(id=request.user.id).exists():
            return Response(
                {"error": "구독 중이 아닙니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        color_serializer = UserChannelColorSerializer(
            UserChannel.objects.get(channel=channel, user=request.user),
            data=request.data,
            partial=True,
            context={"request": request},
        )

        color_serializer.is_valid(raise_exception=True)
        color_serializer.save()
        return Response(color_serializer.data)

    @color.mapping.get
    def get_color(self, request, pk):
        """
        # 채널 색상 GET API
        * {id}에는 channel의 id를 넣으면 됨
        * 구독자가 아닌 경우 테마 색상 중 랜덤으로 하나를 반환
        """
        channel = self.get_object()
        if not channel.subscribers.filter(id=request.user.id).exists():
            return Response({"color": random_color()})
        serializer = UserChannelColorSerializer(
            UserChannel.objects.get(channel=channel, user=request.user),
            context={"request": request},
        )
        return Response(serializer.data)