from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notice.models import Notice, NoticeImage
from apps.channel.models import Channel
from apps.notice.serializers import NoticeSerializer
from apps.notice.permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q


class NoticeIdViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
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
        queryset = self.get_queryset()
        param = request.query_params

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if channel.is_private and not (channel.managers.filter(id=request.user.id)):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        data = queryset.filter(channel=channel_pk)
        recent_notices = 10

        if param.get("recent", "") == "True":
            if data.count() > recent_notices:
                data = data[0:recent_notices]

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if channel.is_private and not (channel.managers.filter(id=request.user.id)):
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
        notice_list = self.get_queryset().filter(channel_id=channel_pk)
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(param["q"]) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        if search_keyword:
            if len(search_keyword) >= 2:
                if search_type == "all":
                    notice_list = notice_list.filter(
                        Q(title__icontains=search_keyword)
                        | Q(contents__icontains=search_keyword)
                    )
                elif search_type == "title":
                    notice_list = notice_list.filter(Q(title__icontains=search_keyword))
                elif search_type == "contents":
                    notice_list = notice_list.filter(
                        Q(contents__icontains=search_keyword)
                    )

        if not notice_list.exists():
            return Response(
                {"error": "검색 결과가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        page = self.paginate_queryset(notice_list)

        if page is not None:
            data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(data)

        serializer = self.get_serializer(notice_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserNoticeViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
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
        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request, user_pk):
        """
        # 유저가 구독하고 있는 채널들의 공지사항 검색 API
        * params의 'type'으로 검색 타입 'all', 'title', 'contents'을 받음
        * pararms의 'q'로 검색어를 받음
        """
        notice_list = self.get_queryset()
        param = request.query_params
        search_keyword = self.request.GET.get("q", "")
        search_type = self.request.GET.get("type", "")

        if len(param["q"]) < 2:
            return Response(
                {"error": "검색어를 두 글자 이상 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        if search_keyword:
            if len(search_keyword) >= 2:
                if search_type == "all":
                    notice_list = notice_list.filter(
                        Q(title__icontains=search_keyword)
                        | Q(contents__icontains=search_keyword)
                    )
                elif search_type == "title":
                    notice_list = notice_list.filter(Q(title__icontains=search_keyword))
                elif search_type == "contents":
                    notice_list = notice_list.filter(
                        Q(contents__icontains=search_keyword)
                    )

        page = self.paginate_queryset(notice_list)

        if not notice_list.exists():
            return Response(
                {"error": "검색 결과가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        if page is not None:
            data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(data)

        serializer = self.get_serializer(notice_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
