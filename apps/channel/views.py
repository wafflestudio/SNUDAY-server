from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from apps.channel.models import Channel
from apps.channel.permission import ManagerCanModify
from apps.channel.serializers import ChannelSerializer
from django.contrib import messages
from django.db.models import Q


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [
        ManagerCanModify
    ]

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk):
        channel = self.get_object()

        if channel.subscribers.filter(id=request.user.id).exists():
            return Response({"error" : "이미 구독 중입니다."}, status=status.HTTP_400_BAD_REQUEST)

        channel.subscribers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        channel = self.get_object()

        if not channel.subscribers.filter(id=request.user.id).exists():
            return Response({"error" : "구독 중이 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

        channel.subscribers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

def ChannelList(request):
    qs = request.user.subscribing_channels.all()
    data = ChannelSerializer(qs, many=True).data
    return Response(data)

class ChannelSearchViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [
        ManagerCanModify
    ]

    def get_queryset(self):
        search_keyword =  self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '')
        channel_list = Channel.objects.all()
        if search_keyword:
            if len(search_keyword) >= 2:
                if search_type == 'all':
                    search_channel_list = channel_list.filter(Q(name__icontains = search_keyword) |  Q(description__icontains = search_keyword))
                elif search_type == 'name':
                    search_channel_list = channel_list.filter(Q(name__icontains = search_keyword))
                elif search_type == 'description':
                    search_channel_list = channel_list.filter(Q(description__icontains = search_keyword))
                return search_channel_list
            else:
                messages.error(self.request, '검색어는 두 글자 이상 입력해주세요.')
        return channel_list

    def get_context_data(self, **kwargs):
        search_keyword = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', '')
        context['q'] = search_keyword
        context['type'] =  search_type
        return context
    
    def list(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)