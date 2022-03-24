from rest_framework import serializers

from apps.feedback.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        exclude = ["created_at"]

    def get_user(self):
        return self.context.request.user
