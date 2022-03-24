from django.test import TestCase
from rest_framework.test import APIClient

from apps.channel.models import Channel, UserChannel, ManagerChannel
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
            "managers_id": f'["{self.user.username}"]',
        }

        self.private_channel_data = {
            "name": "wafflestudio 18-5",
            "description": "맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            "is_private": True,
            "managers_id": f'["{self.user.username}"]',
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

    def test_update_user_password_fail(self):
        self.client.force_authenticate(user=self.b)

        password = "newpassword123~"
        update = self.client.patch(
            "/api/v1/users/me/",
            {"password": password},
            format="json",
        )
        self.assertEqual(update.status_code, 400)

    def test_get_users_subscribing_channels(self):
        self.client.force_authenticate(user=self.user)

        channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        UserChannel.objects.create(user=self.user, channel=channel)

        channel_personal = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_personal=True,
        )

        # 개인 채널도 생성한뒤 안보이는거 확인
        UserChannel.objects.create(
            user=self.user,
            channel=channel_personal,
        )

        subscribing = self.client.get("/api/v1/users/me/subscribing_channels/")
        data = subscribing.json()

        self.assertEqual(subscribing.status_code, 200)
        self.assertEqual(len(data), 1)

        others = self.client.get(f"/api/v1/users/{self.b.id}/subscribing_channels/")
        self.assertEqual(others.status_code, 403)

    def test_get_users_managing_channels(self):
        self.client.force_authenticate(user=self.user)

        create = self.client.post("/api/v1/channels/", self.channel_data, format="json")

        channel_personal = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_personal=True,
        )

        # 개인 채널도 생성한뒤 안보이는거 확인
        ManagerChannel.objects.create(
            user=self.user,
            channel=channel_personal,
        )
        managing = self.client.get("/api/v1/users/me/managing_channels/")
        data = managing.json()

        self.assertEqual(managing.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "wafflestudio")

        others = self.client.get(f"/api/v1/users/{self.b.id}/managing_channels/")
        self.assertEqual(others.status_code, 403)

        create_private = self.client.post(
            "/api/v1/channels/", self.private_channel_data, format="json"
        )
        data = create_private.json()
        private_channel = Channel.objects.get(id=data["id"])

        self.client.force_authenticate(user=self.b)
        self.client.post(f"/api/v1/channels/{private_channel.id}/subscribe/")
        self.assertEqual(private_channel.awaiters.count(), 1)

        self.client.force_authenticate(user=self.user)
        managing = self.client.get("/api/v1/users/me/managing_channels/")
        data = managing.json()

        self.assertEqual(managing.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]["name"], private_channel.name)
        self.assertEqual(data[1]["is_private"], True)
        self.assertEqual(data[1]["awaiters_count"], 1)

    def test_get_users_awaiting_channels(self):
        self.client.force_authenticate(user=self.user)

        private_channel_1 = Channel.objects.create(
            name="wafflestudio_private",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_private=True,
        )
        private_channel_2 = Channel.objects.create(
            name="snucse_private", description="서울대학교 컴퓨터공학부 학생회 비밀 채널", is_private=True
        )

        subscribe_1 = self.client.post(
            f"/api/v1/channels/{private_channel_1.id}/subscribe/"
        )
        subscribe_2 = self.client.post(
            f"/api/v1/channels/{private_channel_2.id}/subscribe/"
        )

        awaiting = self.client.get("/api/v1/users/me/awaiting_channels/")
        data = awaiting.json()
        self.assertEqual(awaiting.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]["name"], private_channel_2.name)
        self.assertEqual(data[1]["is_private"], True)
        others = self.client.get(f"/api/v1/users/{self.b.id}/awaiting_channels/")
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

    def test_username_search(self):
        self.client.force_authenticate(user=self.user)
        search_type = "username"
        search_keyword = "test"

        search = self.client.get(
            f"/api/v1/users/search/?type={search_type}&q={search_keyword}",
            format="json",
        )
        data = search.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["username"], "testuser")
        self.assertEqual(data[0]["first_name"], "first")
        self.assertEqual(data[0]["last_name"], "last")
        self.assertEqual(data[0]["email"], "email@email.com")

        self.assertEqual(search.status_code, 200)

        search_keyword = "wrong"
        search = self.client.get(
            f"/api/v1/users/search/?type={search_type}&q={search_keyword}",
            format="json",
        )
        self.assertEqual(search.status_code, 400)

        search_keyword = "s"
        search = self.client.get(
            f"/api/v1/users/search/?type={search_type}&q={search_keyword}",
            format="json",
        )
        self.assertEqual(search.status_code, 400)
