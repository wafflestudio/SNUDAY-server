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
        self.data = {
            "username": "snuday",
            "password": "password",
            "first_name": "Miseung",
            "last_name": "Kim",
            "email": "snuday@snu.ac.kr",
        }
        self.client = APIClient()

    def test_create_user(self):
        create = self.client.post('/api/v1/users/', self.data, format='json')

        self.assertEqual(create.status_code, 201)

    def test_create_without_infos_will_fail(self):
        keys = self.data.keys()
        ds = [self.data.copy() for _ in range(len(keys))]

        for k, d in zip(keys, ds):
            del d[k]

        for d in ds:
            create = self.client.post('/api/v1/users/', d, format='json')

            self.assertEqual(create.status_code, 400)

    def test_create_with_duplicated_email(self):
        data = self.data.copy()
        data.update(email='email@email.com')

        create = self.client.post('/api/v1/users/', data, format='json')

        self.assertEqual(create.status_code, 400)

    def test_create_with_dupliacted_username(self):
        data = self.data.copy()
        data.update(email='testuser')
        create = self.client.post('/api/v1/users/', data, format='json')

        self.assertEqual(create.status_code, 400)

    def test_create_with_malformed_data_will_fail(self):
        data = self.data.copy()
        data.update(email='실패!')

        create = self.client.post('/api/v1/users/', data, format='json')

        self.assertEqual(create.status_code, 400)

    def test_get_user_will_fail_without_login(self):
        get = self.client.get('/api/v1/users/me/')

        self.assertEqual(get.status_code, 401)

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

