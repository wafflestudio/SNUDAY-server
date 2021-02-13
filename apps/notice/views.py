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

    def create(self, request, pk):
        data = request.data.copy()
        data['writer'] = request.user.id
        data['channel'] = Channel.objects.filter(id=pk)[0].id

        serializer = NoticeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def list(self, request, pk):
        queryset = self.get_queryset()
        param = request.query_params

        channel = Channel.objects.filter(id=pk)[0].id
        data = queryset.select_related('channel')

        if param.get('recent', '') == 'True':
            if (data.count() > 10):
                data = data[0:10]

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NoticeIdViewSet(viewsets.GenericViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def list(self, request, pk, pk_2):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=pk)[0].id
        data = queryset.select_related('channel')

        notice = data.filter(id = pk_2)[0]

        serializer = self.get_serializer(notice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk, pk_2):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=pk)[0].id
        data = queryset.select_related('channel')

        notice = data.filter(id = pk_2)[0]

        data = request.data.copy()

        serializer = self.get_serializer(notice, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(notice, serializer.validated_data)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['DELETE'])
    def delete(self, request, pk, pk_2):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=pk)[0].id
        data = queryset.select_related('channel')

        notice = data.filter(id = pk_2)[0]
        notice.delete()

        return Response(status = status.HTTP_200_OK)