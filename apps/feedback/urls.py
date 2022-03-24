from apps.feedback.views import FeedbackView
from django.urls import path, include

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),  # /api/v1/feedback/
]
