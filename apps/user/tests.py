from django.test import TestCase
from rest_framework.test import APIClient

from apps.user.models import User


class UserCreateDeleteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='email@email.com',
            password='password',
            first_name='first',
            last_name='last'
        )
        self.client = APIClient()

    def test_create_user(self):
        create = self.client.post('/api/v1/users/', {
            "username": "snuday",
            "password": "password",
            "first_name": "Miseung",
            "last_name": "Kim",
            "email": "snuday@snu.ac.kr",
        }, format='json')

        self.assertEqual(create.status_code, 201)

    def test_get_user_will_fail_without_login(self):
        get = self.client.get('/api/v1/users/me/')

        self.assertEqual(get.status_code, 403)

    def test_get_user(self):
        self.client.force_authenticate(user=self.user)
        get = self.client.get('/api/v1/users/me/')

        self.assertEqual(get.status_code, 200)

    def test_update_user(self):
        self.client.force_authenticate(user=self.user)

        username = 'apple'
        email = 'samsung@snu.ac.kr'

        update = self.client.put('/api/v1/users/me/', {
            "username": username,
            "email": email,
        }, format='json')

        self.assertEqual(update.status_code, 200)

        user = User.objects.last()
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)

