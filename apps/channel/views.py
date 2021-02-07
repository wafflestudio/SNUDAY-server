from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin

from apps.channel.models import Channel
from apps.channel.serializers import ChannelSerializer


class ChannelViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Channel.objects.prefetch_related(
        Prefetch('subscribers', to_attr='managers')
    )
    serializer_class = ChannelSerializer
