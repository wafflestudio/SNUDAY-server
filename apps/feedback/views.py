from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework import permissions
from apps.feedback.serializers import FeedbackSerializer
from apps.feedback.models import Feedback

# Create your views here.


class FeedbackView(CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Feedback.objects.all()

    def post(self, request):
        """
        로그인한 사용자만 사용할 수 있습니다. content라는 파라미터로 길이 300 이내의 문자열을 받습니다.
        정상적인 경우 201 CREATED와 생성된 피드백을 반환합니다.
        """
        request.data["user"] = request.user.id
        return super().create(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request
        return context
