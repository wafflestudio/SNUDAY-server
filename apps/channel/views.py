from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer
from apps.user.models import User
from apps.user.serializers import UserSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [ManagerCanModify]

    def create(self, request):
        """
        # 채널을 만드는 API
        * `managers_id`는 매니저의 `username`들을 ["user1", "user2"]와 같이 list 형식으로 넣어야 함
        * image는 얻게 된 이미지의 url을 첨부할 것
        * `is_private`은 비공개채널 여부에 대한 설정
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

        data["managers_id"].append(user.username)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        channel = Channel.objects.get(id=serializer.data["id"])

        for manager in data["managers_id"]:
            manager_obj = User.objects.get(username=manager)
            channel.subscribers.add(manager_obj)
            channel.managers.add(manager_obj)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        if "name" in data:
            q_channel = Channel.objects.filter(name=data["name"]).first()

            if q_channel is not None:
                return Response(
                    {"error": "동일한 이름의 채널이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(channel, data=data, partial=True)
        validated_data = serializer.is_valid(raise_exception=True)
        serializer.update(channel, serializer.validated_data)

        if "managers_id" in data:
            current_managers = list(channel.managers.all())
            for manager in current_managers:
                if not manager.username in data["managers_id"]:
                    channel.managers.remove(manager)

            for manager_name in data["managers_id"]:
                manager = User.objects.get(username=manager_name)
                channel.subscribers.add(manager)
                channel.managers.add(manager)

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
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def recommend(self, request):
        """
        # 채널 추천 API
        * 구독자가 가장 많은 5개의 채널들을 추천해줌.
        """
        channels = Channel.objects.filter(is_private=False).order_by(
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
        qs = Channel.objects.all()
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

            if not qs.exists():
                return Response(
                    {"error": "검색 결과가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
                )
        page = self.paginate_queryset(qs)

        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)
