from django.test import TestCase
from rest_framework.test import APIClient

from apps.user.models import User


class TokenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='email@email.com',
            password='password',
            first_name='first',
            last_name='last',
            is_active=True,
        )

        self.client = APIClient()

    def test_login(self):
        login = self.client.post('/api/v1/users/login/', {
            'username': self.user.username,
            'password': 'password'
        }, format='json')

        self.assertEqual(login.status_code, 200)

        access = login.data['access']

        users_me = self.client.get('/api/v1/users/me/', HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(users_me.status_code, 200)

    def test_fresh(self):
        login = self.client.post('/api/v1/users/login/', {
            'username': self.user.username,
            'password': 'password'
        }, format='json')

        self.assertEqual(login.status_code, 200)

        refresh_token = login.data['refresh']

        refresh = self.client.post('/api/v1/users/refresh/', {
            'refresh': refresh_token
        }, format='json')

        self.assertEqual(login.status_code, 200)
