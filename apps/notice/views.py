from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notice.models import Notice, NoticeImage
from apps.channel.models import Channel
from apps.notice.serializers import NoticeSerializer, NoticeChannelNameSerializer
from apps.notice.permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from apps.core.utils import get_object_or_400


class NoticeIdViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return NoticeChannelNameSerializer
        return NoticeSerializer

    permission_classes = [IsOwnerOrReadOnly()]

    def get_permissions(self):
        return self.permission_classes

    def create(self, request, channel_pk, pk=None):
        data = request.data.copy()
        data["writer"] = request.user.id
        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not channel.managers.filter(id=request.user.id).exists():
            return Response(
                {"error": "Only managers can write a notice."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data["channel"] = channel.id
        serializer = NoticeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, channel_pk):
        channel = get_object_or_400(Channel, id=channel_pk)

        if (
            channel.is_private
            and not channel.managers.filter(id=request.user.id).exists()
            and not channel.subscribers.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        qs = self.get_queryset().filter(channel=channel)

        page = self.paginate_queryset(qs)

        if page is not None:
            data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(data)

        data = self.get_serializer(qs, many=True)
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if (
            channel.is_private
            and not channel.managers.filter(id=request.user.id).exists()
            and not channel.subscribers.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        data = queryset.filter(channel=channel_pk)
        notice = data.filter(id=pk).first()

        if notice == None:
            return Response(
                {"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(notice)
        self.check_object_permissions(self.request, notice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = queryset.filter(channel=channel_pk)
        notice = data.filter(id=pk).first()

        if notice == None:
            return Response(
                {"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        if data == {}:
            return Response(
                {"error": "The request is not complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(notice, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, notice)
        serializer.update(notice, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = queryset.filter(channel=channel_pk)
        notice = data.filter(id=pk).first()

        if notice == None:
            return Response(
                {"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        self.check_object_permissions(self.request, notice)
        notice.delete()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request, channel_pk):
        """
        # 채널 내 공지사항 검색 API
        * params의 'type'으로 검색 타입 'all', 'title', 'contents'을 받음
        * pararms의 'q'로 검색어를 받음
        """
        qs = self.get_queryset().filter(channel_id=channel_pk)
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(search_keyword) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        if search_keyword:
            if search_type == "all":
                qs = qs.filter(
                    Q(title__icontains=search_keyword)
                    | Q(contents__icontains=search_keyword)
                )
            elif search_type == "title":
                qs = qs.filter(Q(title__icontains=search_keyword))
            elif search_type == "contents":
                qs = qs.filter(Q(contents__icontains=search_keyword))

        page = self.paginate_queryset(qs)

        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)


# bring recent 10 notices
class NoticeRecentViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeChannelNameSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["GET"])
    def recent_notices(self, request, pk=None):
        channel = get_object_or_400(Channel, id=pk)

        if channel.is_private and not (channel.managers.filter(id=request.user.id)):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        data = Notice.objects.filter(channel=channel.id).order_by("-created_at")

        RECENT_NOTICES = 3
        num_items = data.count()

        if num_items > RECENT_NOTICES:
            data = data[:RECENT_NOTICES]

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserNoticeViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeChannelNameSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, user_pk):
        if user_pk != "me":
            return Response(
                {"error": "Cannot read others' notices"},
                status=status.HTTP_403_FORBIDDEN,
            )

        channel_list = request.user.subscribing_channels.all().values_list(
            "id", flat=True
        )

        qs = Notice.objects.filter(channel__in=list(channel_list))
        page = self.paginate_queryset(qs)
        data = self.get_serializer(page, many=True).data

        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"])
    def search(self, request, user_pk):
        """
        # 유저가 구독하고 있는 채널들의 공지사항 검색 API
        * params의 'type'으로 검색 타입 'all', 'title', 'contents'을 받음
        * pararms의 'q'로 검색어를 받음
        """
        if user_pk != "me":
            return Response(
                {"error": "Cannot read others' notices"},
                status=status.HTTP_403_FORBIDDEN,
            )

        channel_list = request.user.subscribing_channels.all().values_list(
            "id", flat=True
        )

        qs = Notice.objects.filter(channel__in=list(channel_list))
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
                    Q(title__icontains=search_keyword)
                    | Q(contents__icontains=search_keyword)
                )
            elif search_type == "title":
                qs = qs.filter(Q(title__icontains=search_keyword))
            elif search_type == "contents":
                qs = qs.filter(Q(contents__icontains=search_keyword))

        page = self.paginate_queryset(qs)

        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)
