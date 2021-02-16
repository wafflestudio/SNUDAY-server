from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [ManagerCanModify]

    @action(detail=True, methods=["post"])
    def subscribe(self, request, pk):
        channel = self.get_object()

        if channel.is_private:
            return Response("비공개 채널은 구독할 수 없습니다.", status=status.HTTP_403_FORBIDDEN)

        if channel.subscribers.filter(id=request.user.id).exists():
            return Response("이미 구독 중입니다.", status=status.HTTP_400_BAD_REQUEST)

        channel.subscribers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        channel = self.get_object()

        if not channel.subscribers.filter(id=request.user.id).exists():
            return Response("구독 중이 아닙니다.", status=status.HTTP_400_BAD_REQUEST)

        channel.subscribers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def ChannelList(request):
    qs = request.user.subscribing_channels.all()
    data = ChannelSerializer(qs, many=True).data
    return Response(data)
