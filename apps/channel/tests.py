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

    def test_create_without_manager_will_suc(self):
        data = self.data.copy()
        data.update(managers_id=[])

        create = self.client.post('/api/v1/channels/', data, format='json')
        self.assertEqual(create.status_code, 201)


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

        self.public_channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        self.public_channel.managers.set([self.user])

        self.private_channel = Channel.objects.create(
            name="wafflestudio18-5",
            description="와플스튜디오 18.5기 활동 채널입니다.",
            is_private=True
        )
        self.private_channel.managers.set([self.user])
        self.client = APIClient()

    def test_delete_without_permission_will_fail(self):
        self.client.force_authenticate(user=self.b)

        delete = self.client.delete(f'/api/v1/channels/{self.public_channel.id}/')
        self.assertEqual(delete.status_code, 403)

    def test_delete(self):
        self.client.force_authenticate(user=self.user)

        delete = self.client.delete(f'/api/v1/channels/{self.public_channel.id}/')
        self.assertEqual(delete.status_code, 204)

        self.assertEqual(Channel.objects.count(), 1)

    def test_update_without_permission_will_fail(self):
        self.client.force_authenticate(user=self.b)

        update = self.client.patch(f'/api/v1/channels/{self.public_channel.id}/', {
            'description': '호야'
        }, format='json')
        self.assertEqual(update.status_code, 403)

    def test_update(self):
        self.client.force_authenticate(user=self.user)

        content = '내가 할 수 있는 건'

        update = self.client.patch(f'/api/v1/channels/{self.public_channel.id}/', {
            'description': content
        }, format='json')
        self.assertEqual(update.status_code, 200)

        channel = Channel.objects.first()
        self.assertEqual(channel.description, content)

    def test_public_subscribe(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.public_channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)

        self.assertEqual(self.public_channel.subscribers.count(), 1)

    def test_public_subscribe_twice_will_fail(self):
        self.client.force_authenticate(user=self.b)

        self.client.post(f"/api/v1/channels/{self.public_channel.id}/subscribe/")
        subscribe = self.client.post(f"/api/v1/channels/{self.public_channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 400)

    def test_public_unsubscribe(self):
        self.client.force_authenticate(user=self.b)
        self.client.post(f"/api/v1/channels/{self.public_channel.id}/subscribe/")

        subscribe = self.client.delete(f"/api/v1/channels/{self.public_channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 204)

    def test_public_unsubscribe_without_subscribe_will_fail(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.delete(f"/api/v1/channels/{self.public_channel.id}/subscribe/")

        self.assertEqual(subscribe.status_code, 400)
    
    def test_private_subscribe_and_unsubscribe(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.private_channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)
        self.assertEqual(self.private_channel.awaiters.count(), 1)
        self.assertEqual(self.private_channel.subscribers.count(), 0)

        unsubscribe = self.client.delete(f"/api/v1/channels/{self.private_channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)
        self.assertEqual(self.private_channel.awaiters.count(), 0)
        self.assertEqual(self.private_channel.subscribers.count(), 0)

    def test_private_subscribe_and_allow(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.private_channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)
        self.assertEqual(self.private_channel.awaiters.count(), 1)

        self.client.force_authenticate(user=self.user)
        allow = self.client.post(f"/api/v1/channels/{self.private_channel.id}/awaiters/allow/{self.b.id}/")
        self.assertEqual(allow.status_code, 200)
        self.assertEqual(self.private_channel.awaiters.count(), 0)
        self.assertEqual(self.private_channel.subscribers.count(), 1)
    
    def test_private_subscribe_and_disallow(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.private_channel.id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)
        self.assertEqual(self.private_channel.awaiters.count(), 1)

        self.client.force_authenticate(user=self.user)
        allow = self.client.delete(f"/api/v1/channels/{self.private_channel.id}/awaiters/allow/{self.b.id}/")
        self.assertEqual(allow.status_code, 200)
        self.assertEqual(self.private_channel.awaiters.count(), 0)
        self.assertEqual(self.private_channel.subscribers.count(), 0)


class ChannelSearchTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='email@email.com',
            password='password',
            first_name='first',
            last_name='last'
        )

        self.channel1 = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        self.channel1.managers.set([self.user])

        self.channel2 = Channel.objects.create(
            name="와플스튜디오 2021 Winter project",
            description="와플스튜디오 겨울 프로젝트 진행을 위한 채널입니다."
        )
        self.channel2.managers.set([self.user])

        self.channel3 = Channel.objects.create(
            name="서울대학교 총학생회",
            description="안녕하세요, 서울대학교 총학생회입니다."
        )
        self.channel3.managers.set([self.user])

    def test_all_search(self):
        type = 'all'
        keyword = '와플'
        all_search = self.client.get(f"/api/v1/search/?type={type}&q={keyword}")

        self.assertEqual(all_search.status_code, 200)

    def test_description_search(self):
        type = 'description'
        keyword = '맛있는'
        description_search = self.client.get(f"/api/v1/search/?type={type}&q={keyword}")

        self.assertEqual(description_search.status_code, 200)

    def test_name_search(self):
        type = 'name'
        keyword = 'wafflestudio'
        name_search = self.client.get(f"/api/v1/search/?type={type}&q={keyword}")

        self.assertEqual(name_search.status_code, 200)

    def test_less_than_two_letters(self):
        type = 'all'
        keyword = '와'
        less_than_two_search = self.client.get(f"/api/v1/search/?type={type}&q={keyword}")

        self.assertEqual(less_than_two_search.status_code, 400)

    def test_less_than_two_letters_2(self):
        type = 'all'
        keyword = '검색되지않는단어'
        not_search = self.client.get(f"/api/v1/search/?type={type}&q={keyword}")

        self.assertEqual(not_search.status_code, 400)
