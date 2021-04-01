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
            "start_time",
            "due_time",
        )


# serializer for event data with CHANNEL NAME
class EventChannelNameSerializer(EventSerializer):
    channel_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = EventSerializer.Meta.fields + ("channel_name",)

    def get_channel_name(self, event):
        return event.channel.name
