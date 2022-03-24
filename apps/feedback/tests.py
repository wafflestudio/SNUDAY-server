from rest_framework import status
from apps.feedback.models import Feedback
from apps.user.models import User
import json
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.test import APIClient


class FeedbackTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            email="email@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

    def test_feedback_created(self):
        self.client.force_authenticate(user=self.user)
        content = "best app in the world."
        response = self.client.post(
            "/api/v1/feedback/",
            data={"content": content},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["user"], self.user.id)
        self.assertEqual(data["content"], content)
        self.assertEqual(Feedback.objects.count(), 1)

    def test_feedback_bad_request(self):
        self.client.force_authenticate(user=self.user)
        content = ""
        response = self.client.post(
            "/api/v1/feedback/",
            data={"content": content},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Feedback.objects.count(), 0)
        content = "a" * 301
        response = self.client.post(
            "/api/v1/feedback/",
            data={"content": content},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_feedback_unauthorized(self):
        content = "best app in the world."
        response = self.client.post(
            "/api/v1/feedback/",
            data={"content": content},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Feedback.objects.count(), 0)
