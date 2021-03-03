from rest_framework import serializers

from apps.event.models import Event
from apps.user.models import User
from apps.channel.models import Channel


class EventSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event
        fields = (
            'id',
            'contents',
            'channel',
            'writer',
            'created_at',
            'updated_at',
            'has_time',
            'start_date',
            'due_date',
        )



    
