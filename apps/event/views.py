from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.event.models import Event
from apps.channel.models import Channel
from apps.event.serializers import EventSerializer
from apps.notice.permission import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated

class EventViewSet(viewsets.GenericViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
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
            return Response({"error": "Only managers can create an event."}, status=status.HTTP_403_FORBIDDEN)
        
        data['channel'] = channel.id
        data['has_time'] = request.POST.get('has_time', False)
        data['start_date'] = request.POST.get('start_date', None)
        data['due_date'] = request.POST.get('due_date', None)

        if data['has_time'] and ((not data['start_date']) or (not data['due_date'])):
            return Response({"error": "Time information is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EventSerializer(data=data)
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
        event = data.filter(id = pk).first()

        if event == None:
            return Response({"error": "Wrong Event ID."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(event)
        self.check_object_permissions(self.request, event)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = queryset.filter(channel = channel_pk)
        event = data.filter(id = pk).first()

        if event == None:
            return Response({"error": "Wrong Event ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()

        if data == {}:
              return Response({"error": "The request is not complete."}, status=status.HTTP_400_BAD_REQUEST)

        if data['has_time'] and ((not data['start_date']) or (not data['due_date'])):
            return Response({"error": "Time information is required."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(event, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, event)
        serializer.update(event, serializer.validated_data)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, channel_pk, pk):
        queryset = self.get_queryset()

        channel = Channel.objects.filter(id=channel_pk).first()

        if channel == None:
            return Response({"error": "Wrong Channel ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = queryset.filter(channel = channel_pk)
        event = data.filter(id = pk).first()

        if event == None:
            return Response({"error": "Wrong Event ID."}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(self.request, event)
        event.delete()

        return Response(status = status.HTTP_200_OK)

class UserEventViewSet(viewsets.GenericViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def list(self, request, user_pk):
        if user_pk != 'me':
            return Response({"error": "Cannot read others\' events"}, status=status.HTTP_403_FORBIDDEN)

        channel_list = request.user.subscribing_channels.all().values_list('id', flat = True)

        qs = Event.objects.filter(channel__in = list(channel_list))
        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)