from rest_framework import serializers

from apps.event.models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "memo",
            "channel",
            "writer",
            "created_at",
            "updated_at",
            "has_time",
            "start_date",
            "due_date",
        )
