from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.channel.serializers import ChannelSerializer
from apps.core.mixins import SerializerChoiceMixin
from apps.user.models import User
from apps.user.serializers import UserSerializer


class UserViewSet(SerializerChoiceMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_classes = {
        'default': UserSerializer,
        'channels': ChannelSerializer,
    }

    def get_permissions(self):
        if self.action in ('create', 'login', 'refresh'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, pk=None):
        user = request.user if pk == 'me' else self.get_object()
        return Response(self.get_serializer(user).data)

    def update(self, request, pk=None):
        if pk != 'me':
            return Response('다른 사람의 정보를 업데이트 할 수 없습니다.', status=status.HTTP_403_FORBIDDEN)

        user = request.user
        data = request.data.copy()

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
