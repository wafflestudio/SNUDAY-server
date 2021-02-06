from django.test import TestCase
from rest_framework.test import APIClient

from apps.user.models import User


class ChannelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='email@email.com',
            password='password',
            first_name='first',
            last_name='last'
        )

        self.data = {
            "name": "wafflestudio",
            "description": "맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            "is_private": False
        }
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_channel(self):
        create = self.client.post('/channels/', self.data, format='json')
        self.assertEqual(create.status_code, 201)
