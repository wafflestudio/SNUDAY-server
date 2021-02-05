from django.test import TestCase
from rest_framework.test import APIClient


class UserCreateDeleteTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        create = self.client.post('/users/', {
            "username": "snuday",
            "password": "password",
            "first_name": "Miseung",
            "last_name": "Kim",
            "email": "snuday@snu.ac.kr",
            "faculty": "자유전공학부",
            "major": "자유전공학부"
        }, format='json')

        self.assertEqual(create.status_code, 201)
