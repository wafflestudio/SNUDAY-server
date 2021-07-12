from django.test import TestCase
from rest_framework.test import APIClient

from apps.channel.models import Channel, UserChannel
from apps.user.models import User, EmailInfo


class UserCreateDeleteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="email@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.b = User.objects.create_user(
            username="testuser2",
            email="email2@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.data = {
            "username": "snuday",
            "password": "password",
            "first_name": "Miseung",
            "last_name": "Kim",
            "email": "snuday@snu.ac.kr",
        }

        EmailInfo.of("snuday", True)

        self.channel_data = {
            "name": "wafflestudio",
            "description": "맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            "is_private": False,
            "managers_id": [self.user.id],
        }

        self.client = APIClient()

    def test_create_user(self):
        create = self.client.post("/api/v1/users/", self.data, format="json")

        self.assertEqual(create.status_code, 201)
        self.assertEqual(Channel.objects.count(), 1)

    def test_create_without_infos_will_fail(self):
        keys = self.data.keys()
        ds = [self.data.copy() for _ in range(len(keys))]

        for k, d in zip(keys, ds):
            del d[k]

        for d in ds:
            create = self.client.post("/api/v1/users/", d, format="json")

            self.assertEqual(create.status_code, 400)

    def test_create_with_duplicated_email(self):
        data = self.data.copy()
        data.update(email="email@email.com")

        create = self.client.post("/api/v1/users/", data, format="json")

        self.assertEqual(create.status_code, 400)

    def test_create_with_short_password(self):
        data = self.data.copy()
        data.update(password="short")

        create = self.client.post("/api/v1/users/", data, format="json")

        self.assertEqual(create.status_code, 400)

    def test_create_with_dupliacted_username(self):
        data = self.data.copy()
        data.update(email="testuser")
        create = self.client.post("/api/v1/users/", data, format="json")

        self.assertEqual(create.status_code, 400)

    def test_create_with_malformed_data_will_fail(self):
        data = self.data.copy()
        data.update(email="실패!")

        create = self.client.post("/api/v1/users/", data, format="json")

        self.assertEqual(create.status_code, 400)

    def test_get_user_will_fail_without_login(self):
        get = self.client.get("/api/v1/users/me/")

        self.assertEqual(get.status_code, 401)

    def test_get_user(self):
        self.client.force_authenticate(user=self.user)
        get = self.client.get("/api/v1/users/me/")

        self.assertEqual(get.status_code, 200)

    def test_update_user(self):
        self.client.force_authenticate(user=self.b)

        username = "apple"
        email = "samsung@snu.ac.kr"
        EmailInfo.objects.create(email_prefix="samsung", is_verified=True)
        update = self.client.patch(
            "/api/v1/users/me/",
            {
                "username": username,
                "email": email,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 200)

        user = User.objects.last()
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)

        update = self.client.patch(
            "/api/v1/users/2342/",
            {
                "username": username,
                "email": email,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 403)

    def test_get_users_subscribing_channels(self):
        self.client.force_authenticate(user=self.user)

        channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        UserChannel.objects.create(user=self.user, channel=channel)

        subscribing = self.client.get("/api/v1/users/me/subscribing_channels/")
        data = subscribing.json()

        self.assertEqual(subscribing.status_code, 200)
        self.assertEqual(len(data), 1)

        others = self.client.get(f"/api/v1/users/{self.b.id}/subscribing_channels/")
        self.assertEqual(others.status_code, 403)

    def test_get_users_managing_channels(self):
        self.client.force_authenticate(user=self.user)

        create = self.client.post("/api/v1/channels/", self.channel_data, format="json")

        managing = self.client.get("/api/v1/users/me/managing_channels/")
        data = managing.json()

        self.assertEqual(managing.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "wafflestudio")

        others = self.client.get(f"/api/v1/users/{self.b.id}/managing_channels/")
        self.assertEqual(others.status_code, 403)

    def test_change_password(self):
        self.client.force_authenticate(user=self.b)

        old_password = "password"
        new_password = "password2"
        wrong_password = "wrongpassword"

        update = self.client.patch(
            "/api/v1/users/1/change_password/",
            {
                "old_password": old_password,
                "new_password": new_password,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 403)
        user = User.objects.last()
        self.assertTrue(user.check_password(old_password))

        update = self.client.patch(
            "/api/v1/users/me/change_password/",
            {
                "old_password": wrong_password,
                "new_password": new_password,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 400)
        user = User.objects.last()
        self.assertTrue(user.check_password(old_password))

        update = self.client.patch(
            "/api/v1/users/me/change_password/",
            {
                "old_password": "short",
                "new_password": "short",
            },
            format="json",
        )

        self.assertEqual(update.status_code, 400)
        user = User.objects.last()
        self.assertTrue(user.check_password(old_password))

        update = self.client.patch(
            "/api/v1/users/me/change_password/",
            {
                "old_password": old_password,
                "new_password": old_password,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 400)
        user = User.objects.last()
        self.assertTrue(user.check_password(old_password))

        update = self.client.patch(
            "/api/v1/users/me/change_password/",
            {
                "old_password": old_password,
                "new_password": new_password,
            },
            format="json",
        )

        self.assertEqual(update.status_code, 200)
        user = User.objects.last()
        self.assertTrue(user.check_password(new_password))
