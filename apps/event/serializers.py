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


class EventChannelNameSerializer(serializers.ModelSerializer):
    channel_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "memo",
            "channel",
            "channel_name",
            "writer",
            "created_at",
            "updated_at",
            "has_time",
            "start_date",
            "due_date",
        )

    def get_channel_name(self, event):
        return event.channel.name
