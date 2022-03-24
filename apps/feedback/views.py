from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework import permissions
from apps.feedback.serializers import FeedbackSerializer
from apps.feedback.models import Feedback

# Create your views here.


class FeedbackView(CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request
        return context
