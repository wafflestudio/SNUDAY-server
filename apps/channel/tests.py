from django.test import TestCase
from rest_framework.test import APIClient

from apps.channel.models import Channel
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
            "is_private": False,
            "managers_id": [self.user.id]
        }
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_channel(self):
        create = self.client.post('/api/v1/channels/', self.data, format='json')
        self.assertEqual(create.status_code, 201)

    def test_create_without_manager_will_fail(self):
        data = self.data.copy()
        data.update(managers_id=[])

        create = self.client.post('/api/v1/channels/', data, format='json')
        self.assertEqual(create.status_code, 400)


class ChannelPermissionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='email@email.com',
            password='password',
            first_name='first',
            last_name='last'
        )

        self.b = User.objects.create_user(
            username='testuser2',
            email='email2@email.com',
            password='password',
            first_name='first',
            last_name='last'
        )

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        self.channel.managers.set([self.user])

        self.client = APIClient()

    def test_delete_without_permission_will_fail(self):
        self.client.force_authenticate(user=self.b)

        delete = self.client.delete(f'/api/v1/channels/{self.channel.id}/')
        self.assertEqual(delete.status_code, 403)

    def test_delete(self):
        self.client.force_authenticate(user=self.user)

        delete = self.client.delete(f'/api/v1/channels/{self.channel.id}/')
        self.assertEqual(delete.status_code, 204)

        self.assertEqual(Channel.objects.count(), 0)

    def test_update_without_permission_will_fail(self):
        self.client.force_authenticate(user=self.b)

        update = self.client.patch(f'/api/v1/channels/{self.channel.id}/', {
            'description': '호야'
        }, format='json')
        self.assertEqual(update.status_code, 403)

    def test_update(self):
        self.client.force_authenticate(user=self.user)

        content = '내가 할 수 있는 건'

        update = self.client.patch(f'/api/v1/channels/{self.channel.id}/', {
            'description': content
        }, format='json')
        self.assertEqual(update.status_code, 200)

        channel = Channel.objects.last()
        self.assertEqual(channel.description, content)

    def test_subscribe(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)

        self.assertEqual(self.channel.subscribers.count(), 1)

    def test_subscribe_twice_will_fail(self):
        self.client.force_authenticate(user=self.b)

        self.client.post(f"/api/v1/channels/{self.channel.id}/subscribe/")
        subscribe = self.client.post(f"/api/v1/channels/{self.channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 400)

    def test_unsubscribe(self):
        self.client.force_authenticate(user=self.b)
        self.client.post(f"/api/v1/channels/{self.channel.id}/subscribe/")

        subscribe = self.client.delete(f"/api/v1/channels/{self.channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 204)

    def test_unsubscribe_without_subscribe_will_fail(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.delete(f"/api/v1/channels/{self.channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 400)
