from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.user.models import User
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer
from apps.user.serializers import UserSerializer
from django.contrib import messages
from django.db.models import Q


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [ManagerCanModify]

    def create(self, request):
        user = request.user
        data = request.data.copy()

        data["managers_id"].append(user.id)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        channel = Channel.objects.get(id=serializer.data["id"])
        for manager in data["managers_id"]:
            channel.subscribers.add(manager)
            channel.managers.add(manager)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        channel = self.get_object()
        data = request.data.copy()

        serializer = self.get_serializer(channel, data=data, partial=True)
        validated_data = serializer.is_valid(raise_exception=True)
        serializer.update(channel, serializer.validated_data)

        if "managers_id" in data:
            managers = list(channel.managers.all())
            for manager in managers:
                if not manager in data["managers_id"]:
                    channel.managers.remove(manager)

            for manager in data["managers_id"]:
                channel.subscribers.add(manager)
                channel.managers.add(manager)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def subscribe(self, request, pk):
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
        channel = self.get_object()
        awaiters = channel.awaiters
        serializer = UserSerializer(awaiters, partial=True, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["post"], url_path="awaiters/allow/(?P<user_pk>[^/.]+)"
    )
    def allow(self, request, pk, user_pk):
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
        channels = Channel.objects.filter(is_private=False).order_by(
            "-subscribers_count"
        )[:5]
        serializer = self.get_serializer(channels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def ChannelList(request):
    qs = request.user.subscribing_channels.all()
    data = ChannelSerializer(qs, many=True).data
    return Response(data)


class ChannelSearchViewSet(viewsets.GenericViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [ManagerCanModify]

    def get_queryset(self):
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")
        channel_list = Channel.objects.all()
        if search_keyword:
            if len(search_keyword) >= 2:
                if search_type == "all":
                    search_channel_list = channel_list.filter(
                        Q(name__icontains=search_keyword)
                        | Q(description__icontains=search_keyword)
                    )
                elif search_type == "name":
                    search_channel_list = channel_list.filter(
                        Q(name__icontains=search_keyword)
                    )
                elif search_type == "description":
                    search_channel_list = channel_list.filter(
                        Q(description__icontains=search_keyword)
                    )
                return search_channel_list
        return channel_list

    def list(self, request):
        qs = self.get_queryset()
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(param["q"]) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        elif not qs:
            return Response(
                {"error": "검색 결과가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
