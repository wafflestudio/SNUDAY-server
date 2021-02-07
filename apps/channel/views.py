from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [
        ManagerCanModify
    ]


@api_view(['GET'])
def ChannelList(request):
    qs = request.user.subscribing_channels.all()
    data = ChannelSerializer(qs, many=True).data
    return Response(data)
