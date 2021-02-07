from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notice.models import Notice, NoticeImage
from apps.channel.models import Channel
from apps.notice.serializers import NoticeSerializer
from apps.notice.permission import IsOwnerOrReadOnly



class NoticeViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def create(self, request, pk=None):
        data = request.data.copy()
        data['writer'] = request.user
        data['channel'] = Channel.objects.filter(id=pk)

        serializer = NoticeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def list(self, request, pk=None):
        queryset = self.get_queryset()
        
        channel = Channel.objects.filter(id=pk)
        data = queryset.select_related(channel=channel)
        serializer = self.get_serializer(data, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
