from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.event.serializers import EventSerializer, EventChannelNameSerializer
from apps.core.utils import get_object_or_400
from apps.event.models import Event
from apps.event.serializers import EventSerializer
from apps.notice.permission import IsOwnerOrReadOnly
from datetime import datetime, timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class EventViewSet(generics.RetrieveAPIView, viewsets.GenericViewSet):
    queryset = Event.objects.all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EventChannelNameSerializer
        return EventSerializer

    permission_classes = [
        IsOwnerOrReadOnly,
    ]

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def create(self, request, channel_pk, pk=None):
        data = request.data.copy()
        data["writer"] = request.user.id
        channel = Channel.objects.filter(id=channel_pk).first()

        if "start_date" not in data or "due_date" not in data:
            return Response(
                {"error": "Date information is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["start_date"] = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        data["due_date"] = datetime.strptime(data["due_date"], "%Y-%m-%d").date()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not channel.managers.filter(id=request.user.id).exists():
            return Response(
                {"error": "Only managers can create an event."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data["channel"] = channel.id
        data["has_time"] = request.data.get("has_time", False)

        if data["has_time"] is True:
            data["start_time"] = request.data.get("start_time")
            data["due_time"] = request.data.get("due_time")

            if (data["start_time"] is None) or (data["due_time"] is None):
                return Response(
                    {"error": "Time information is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data["start_time"] = datetime.strptime(data["start_time"], "%H:%M").time()
            data["due_time"] = datetime.strptime(data["due_time"], "%H:%M").time()
            start_datetime = datetime.combine(data["start_date"], data["start_time"])
            due_datetime = datetime.combine(data["due_date"], data["due_time"])

        else:
            data["start_time"] = None
            data["due_time"] = None

            start_datetime = data["start_date"]
            due_datetime = data["due_date"]

        if start_datetime > due_datetime:
            return Response(
                {"error": "The event must end after its beginning."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, channel_pk):
        """
        # 특정 채널의 이벤트를 반환하는 API
        * query parameter가 주어지지 않으면 이번 달의 일정을 반환합니다.
        * query parameter로 date = yyyy-mm-dd 형식으로 주어지면 그 날이 포함된 일정을 반환합니다.(하루짜리 일정은 반환하지 않습니다.)
        * query parameter로 month = yyyy-mm 형식으로 주어지면 그 달이 포함된 일정을 반환합니다.
        """
        channel = get_object_or_400(Channel, id=channel_pk)

        date = self.request.GET.get("date", "")
        month = self.request.query_params.get("month", "")

        if channel.is_private and not (
            channel.managers.filter(id=request.user.id).exists()
            or channel.subscribers.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        qs = self.get_queryset().filter(channel=channel)

        # 특정 날짜
        if date:
            start_date = timezone.make_aware(datetime.strptime(date, "%Y-%m-%d"))
            due_date = start_date
            qs = qs.filter(start_date__lt=due_date, due_date__gt=start_date)

        # 특정 달
        elif month:
            strip_month_begin = datetime.strptime(month, "%Y-%m")
            month_begin = timezone.make_aware(strip_month_begin) - timedelta(days=7)

            next_month = strip_month_begin + relativedelta(months=1)
            month_end = timezone.make_aware(next_month) + timedelta(days=7)

            qs = qs.filter(start_date__lte=month_end) & qs.filter(
                due_date__gte=month_begin
            )

        # 따로 parameter가 없는 경우, 기본적으로는 현재 날짜의 달의 일정을 가져오도록
        else:
            today = datetime.today()
            strip_month_begin = datetime(today.year, today.month, 1)
            month_begin = timezone.make_aware(strip_month_begin) - timedelta(days=7)

            next_month = strip_month_begin + relativedelta(months=1)
            month_end = timezone.make_aware(next_month) + timedelta(days=7)

            qs = qs.filter(start_date__lte=month_end) & qs.filter(
                due_date__gte=month_begin
            )

        page = self.paginate_queryset(qs)

        if page is not None:
            data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(data)

        data = self.get_serializer(qs, many=True)
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, channel_pk, pk):
        channel = get_object_or_400(Channel, id=channel_pk)

        if channel.is_private and not (
            channel.managers.filter(id=request.user.id).exists()
            or channel.subscribers.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )

        return super().retrieve(request, request, channel_pk, pk)

    def patch(self, request, channel_pk, pk):
        queryset = self.get_queryset()
        data = self.request.data.copy()
        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = queryset.filter(channel=channel_pk)
        event = data.filter(id=pk).first()

        if event == None:
            return Response(
                {"error": "Wrong Event ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()

        if data == {}:
            return Response(
                {"error": "The request is not complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["has_time"] = request.data.get("has_time", False)
        data["start_date"] = request.data.get("start_date")
        data["due_date"] = request.data.get("due_date")

        if data["start_date"] is not None:
            data["start_date"] = datetime.strptime(
                data["start_date"], "%Y-%m-%d"
            ).date()
        else:
            data["start_date"] = event.start_date

        if data["due_date"] is not None:
            data["due_date"] = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        else:
            data["due_date"] = event.due_date

        if data["has_time"] is True:
            data["start_time"] = request.data.get("start_time")
            data["due_time"] = request.data.get("due_time")

            if data["start_time"] is not None:
                data["start_time"] = datetime.strptime(
                    data["start_time"], "%H:%M"
                ).time()
            else:
                data["start_time"] = event.start_time

            if data["due_time"] is not None:
                data["due_time"] = datetime.strptime(data["due_time"], "%H:%M").time()
            else:
                data["due_time"] = event.due_time

            if (data["start_time"] is None) or (data["due_time"] is None):
                return Response(
                    {"error": "Time information is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            start_datetime = datetime.combine(data["start_date"], data["start_time"])
            due_datetime = datetime.combine(data["due_date"], data["due_time"])

        else:
            data["start_time"] = None
            data["due_time"] = None

            start_datetime = data["start_date"]
            due_datetime = data["due_date"]

        if start_datetime > due_datetime:
            return Response(
                {"error": "The event must end after its beginning."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(event, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, event)
        serializer.update(event, serializer.validated_data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response(
                {"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        data = queryset.filter(channel=channel_pk)
        event = data.filter(id=pk).first()

        if event == None:
            return Response(
                {"error": "Wrong Event ID."}, status=status.HTTP_400_BAD_REQUEST
            )

        self.check_object_permissions(self.request, event)
        event.delete()

        return Response(status=status.HTTP_200_OK)


class UserEventViewSet(viewsets.GenericViewSet):
    queryset = Event.objects.all()
    serializer_class = EventChannelNameSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, user_pk):
        """
        # 특정 사람이 구독하고 있는 채널들의 이벤트를 반환하는 API
        * query parameter가 주어지지 않으면 이번 달의 일정을 반환합니다.
        * query parameter로 date = yyyy-mm-dd 형식으로 주어지면 그 날이 포함된 일정을 반환합니다.(하루짜리 일정은 반환하지 않습니다.)
        * query parameter로 month = yyyy-mm 형식으로 주어지면 그 달이 포함된 일정을 반환합니다.
        """
        if user_pk != "me":
            return Response(
                {"error": "Cannot read others' events"},
                status=status.HTTP_403_FORBIDDEN,
            )

        date = self.request.GET.get("date", "")
        month = self.request.query_params.get("month", "")

        channel_list = request.user.subscribing_channels.all().values_list(
            "id", flat=True
        )

        qs = Event.objects.filter(channel__in=list(channel_list))

        if date:
            start_date = timezone.make_aware(datetime.strptime(date, "%Y-%m-%d"))
            due_date = start_date
            qs = qs.filter(start_date__lt=due_date, due_date__gt=start_date)
        elif month:
            strip_month_begin = datetime.strptime(month, "%Y-%m")
            month_begin = timezone.make_aware(strip_month_begin) - timedelta(days=7)

            next_month = strip_month_begin + relativedelta(months=1)
            month_end = timezone.make_aware(next_month) + timedelta(days=7)

            qs = qs.filter(start_date__lte=month_end) & qs.filter(
                due_date__gte=month_begin
            )

        # 따로 parameter가 없는 경우, 기본적으로는 현재 날짜의 달의 일정을 가져오도록
        else:
            today = datetime.today()
            strip_month_begin = datetime(today.year, today.month, 1)
            month_begin = timezone.make_aware(strip_month_begin) - timedelta(days=7)

            next_month = strip_month_begin + relativedelta(months=1)
            month_end = timezone.make_aware(next_month) + timedelta(days=7)

            qs = qs.filter(start_date__lte=month_end) & qs.filter(
                due_date__gte=month_begin
            )

        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
