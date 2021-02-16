from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notice.models import Notice, NoticeImage
from apps.channel.models import Channel
from apps.notice.serializers import NoticeSerializer
from apps.notice.permission import IsOwnerOrReadOnly

class NoticeIdViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [
        IsOwnerOrReadOnly()
    ]

    def get_permissions(self):
        return self.permission_classes

    def create(self, request, channel_pk, pk=None):
        data = request.data.copy()
        data['writer'] = request.user.id
        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        if not channel.managers.filter(id = request.user.id).exists():
            return Response({"error": "Only managers can write a notice."}, status=status.HTTP_403_FORBIDDEN)
        
        data['channel'] = channel.id
        serializer = NoticeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, channel_pk):
        queryset = self.get_queryset()
        param = request.query_params

        channel = Channel.objects.filter(id = channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        if channel.is_private and not (channel.managers.filter(id = request.user.id)):
            return Response({"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN)

        data = queryset.filter(channel = channel_pk)
        recent_notices = 10

        if param.get('recent', '') == 'True':
            if (data.count() > recent_notices):
                data = data[0 : recent_notices]

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id = channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        if channel.is_private and not (channel.managers.filter(id = request.user.id)):
            return Response({"error": "This channel is private."}, status=status.HTTP_403_FORBIDDEN)

        data = queryset.filter(channel = channel_pk)
        notice = data.filter(id = pk).first()

        if notice == None:
            return Response({"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(notice)
        self.check_object_permissions(self.request, notice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = queryset.filter(channel = channel_pk)
        notice = data.filter(id = pk).first()

        if notice == None:
            return Response({"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()

        serializer = self.get_serializer(notice, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, notice)
        serializer.update(notice, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = queryset.filter(channel = channel_pk)
        notice = data.filter(id = pk).first()

        if notice == None:
            return Response({"error": "Wrong Notice ID."}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(self.request, notice)
        notice.delete()
        return Response(status = status.HTTP_200_OK)