from django.test import Client, TestCase
from rest_framework import status
from apps.channel.models import Channel
from apps.user.models import User
from .models import Notice
import json
from rest_framework.test import APIClient


class NoticeTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        self.channel.managers.set([self.manager])

        self.channel_id = self.channel.id

        self.data = {"title": "notice title", "contents": "notice content"}

        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    def test_create_notice(self):
        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            self.data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "notice title")
        self.assertEqual(data["contents"], "notice content")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_notice_incomplete_request(self):
        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            json.dumps(
                {
                    "title": "notice title",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 0)

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            json.dumps(
                {
                    "content": "notice content",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 0)

    def test_no_channel(self):
        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id + 100)),
            self.data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 0)

        response = self.client.get(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id + 100))
        )

        self.assertEqual(response.status_code, 400)

    def test_no_notice(self):
        notice_count = Notice.objects.count()

        response = self.client.get(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(notice_count + 1)
            )
        )

        self.assertEqual(response.status_code, 400)

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(notice_count + 1)
            )
        )

        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(notice_count + 1)
            ),
            {
                "title": "updated updated title",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


class PublicChannelNoticeTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.subscriber = User.objects.create_user(
            username="subscriber",
            email="subscriber@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.watcher = User.objects.create_user(
            username="watcher",
            email="watcher@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
        )
        self.channel.managers.set([self.manager])

        self.channel_id = self.channel.id

        self.data = {"title": "notice title", "contents": "notice content"}

        self.client = APIClient()

        self.notice_1 = Notice.objects.create(
            title="notice title",
            contents="notice content",
            channel=self.channel,
            writer=self.manager,
        )

    def test_manager_patch_notice(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {"title": "updated title", "contents": "updated contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated title")
        self.assertEqual(data["contents"], "updated contents")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {
                "title": "updated updated title",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated updated title")
        self.assertEqual(data["contents"], "updated contents")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_manager_delete_notice(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            {"title": "title will be deleted", "contents": "contents will be deleted"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 2)

        data = response.json()
        delete_notice_id = data["id"]

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(delete_notice_id)
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(response.data)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

    def test_subscriber_notice(self):
        self.client.force_authenticate(user=self.subscriber)
        self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            {"title": "title", "contents": "contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {"title": "updated title", "contents": "updated contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Notice.objects.get(id=self.notice_1.id)

        self.assertEqual(data.title, "notice title")
        self.assertEqual(data.contents, "notice content")

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], self.notice_1.id)
        self.assertEqual(data["title"], "notice title")
        self.assertEqual(data["contents"], "notice content")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_watcher_notice(self):
        self.client.force_authenticate(user=self.watcher)

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            {"title": "title", "contents": "contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {"title": "updated title", "contents": "updated contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Notice.objects.get(id=self.notice_1.id)

        self.assertEqual(data.title, "notice title")
        self.assertEqual(data.contents, "notice content")

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], self.notice_1.id)
        self.assertEqual(data["title"], "notice title")
        self.assertEqual(data["contents"], "notice content")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)


class PrivateChannelNoticeTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.subscriber = User.objects.create_user(
            username="subscriber",
            email="subscriber@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.watcher = User.objects.create_user(
            username="watcher",
            email="watcher@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_private=True,
        )
        self.channel.managers.set([self.manager])

        self.channel_id = self.channel.id

        self.data = {"title": "notice title", "contents": "notice content"}

        self.client = APIClient()

        self.notice_1 = Notice.objects.create(
            title="notice title",
            contents="notice content",
            channel=self.channel,
            writer=self.manager,
        )

    def test_manager_patch_notice(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {"title": "updated title", "contents": "updated contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated title")
        self.assertEqual(data["contents"], "updated contents")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {
                "title": "updated updated title",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated updated title")
        self.assertEqual(data["contents"], "updated contents")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_manager_delete_notice(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            {"title": "title will be deleted", "contents": "contents will be deleted"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 2)

        data = response.json()
        delete_notice_id = data["id"]

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(delete_notice_id)
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(response.data)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

    def test_subscriber_notice(self):
        self.client.force_authenticate(user=self.subscriber)
        response = self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")

        self.assertEqual(response.status_code, 204)

    def test_watcher_notice(self):
        self.client.force_authenticate(user=self.watcher)

        response = self.client.post(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id)),
            {"title": "title", "contents": "contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            ),
            {"title": "updated title", "contents": "updated contents"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Notice.objects.get(id=self.notice_1.id)

        self.assertEqual(data.title, "notice title")
        self.assertEqual(data.contents, "notice content")

        response = self.client.delete(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        notice_count = Notice.objects.count()
        self.assertEqual(notice_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/notices/{}/".format(
                str(self.channel_id), str(self.notice_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            "/api/v1/channels/{}/notices/".format(str(self.channel_id))
        )

        self.assertEqual(response.status_code, 403)


class NoticeSearchTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.subscriber = User.objects.create_user(
            username="subscriber",
            email="subscriber@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.watcher = User.objects.create_user(
            username="watcher",
            email="watcher@email.com",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_private=True,
        )

        self.channel_2 = Channel.objects.create(
            name="서울대학교 총학생회",
            description="총학 파이팅!",
            is_private=False,
        )
        self.channel.managers.set([self.manager])

        self.channel_id = self.channel.id
        self.channel_2_id = self.channel_2.id

        self.client = APIClient()

        self.notice_1 = Notice.objects.create(
            title="와플스튜디오 개강파티",
            contents="3월 12일 저녁 7시",
            channel=self.channel,
            writer=self.manager,
        )

        self.notice_2 = Notice.objects.create(
            title="와플스튜디오 신입 부원 모집",
            contents="3월 13일까지 모집합니다.",
            channel=self.channel,
            writer=self.manager,
        )

        self.notice_3 = Notice.objects.create(
            title="와플스튜디오 로고 캐릭터 선정",
            contents="귀여운 캐릭터!",
            channel=self.channel,
            writer=self.manager,
        )

        self.notice_4 = Notice.objects.create(
            title="맛있는 와플 가게",
            contents="와플 초특가 할인",
            channel=self.channel_2,
            writer=self.manager,
        )

    def test_search_channel_notice_all(self):
        self.client.force_authenticate(user=self.subscriber)
        self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")
        self.client.post(f"/api/v1/channels/{self.channel_2_id}/subscribe/")

        type = "all"
        keyword = "와플"
        all_search = self.client.get(
            f"/api/v1/channels/{self.channel.id}/notices/search/?type={type}&q={keyword}"
        )
        data = all_search.json()["results"]
        self.assertEqual(len(data), 3)

        result_1 = data[0]
        self.assertEqual(result_1["title"], "와플스튜디오 로고 캐릭터 선정")
        self.assertEqual(result_1["contents"], "귀여운 캐릭터!")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(all_search.status_code, 200)

    def test_search_channel_notice_title(self):
        self.client.force_authenticate(user=self.watcher)

        type = "title"
        keyword = "개강파티"
        title_search = self.client.get(
            f"/api/v1/channels/{self.channel.id}/notices/search/?type={type}&q={keyword}"
        )
        data = title_search.json()["results"]
        self.assertEqual(len(data), 1)

        result_1 = data[0]
        self.assertEqual(result_1["title"], "와플스튜디오 개강파티")
        self.assertEqual(result_1["contents"], "3월 12일 저녁 7시")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(title_search.status_code, 200)

    def test_search_channel_notice_contents(self):
        self.client.force_authenticate(user=self.watcher)

        type = "contents"
        keyword = "귀여운"
        contents_search = self.client.get(
            f"/api/v1/channels/{self.channel.id}/notices/search/?type={type}&q={keyword}"
        )
        data = contents_search.json()["results"]
        self.assertEqual(len(data), 1)

        result_1 = data[0]
        self.assertEqual(result_1["title"], "와플스튜디오 로고 캐릭터 선정")
        self.assertEqual(result_1["contents"], "귀여운 캐릭터!")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(contents_search.status_code, 200)

    def test_search_channel_notice_less_than_two_letters(self):
        self.client.force_authenticate(user=self.watcher)

        type = "all"
        keyword = "와"
        less_than_two_search = self.client.get(
            f"/api/v1/channels/{self.channel.id}/notices/search/?type={type}&q={keyword}"
        )
        self.assertEqual(less_than_two_search.status_code, 400)

    def test_search_channel_notice_invalid_keyword(self):
        self.client.force_authenticate(user=self.watcher)

        type = "all"
        keyword = "검색되지않는단어"
        not_search = self.client.get(
            f"/api/v1/channels/{self.channel.id}/notices/search/?type={type}&q={keyword}"
        )
        self.assertEqual(not_search.status_code, 400)

    def test_search_user_notice_all(self):
        self.client.force_authenticate(user=self.watcher)

        type = "all"
        keyword = "와플"
        all_search = self.client.get(
            f"/api/v1/users/me/notices/search/?type={type}&q={keyword}"
        )
        data = all_search.json()["results"]
        self.assertEqual(len(data), 4)

        result_1 = data[1]
        self.assertEqual(result_1["title"], "와플스튜디오 로고 캐릭터 선정")
        self.assertEqual(result_1["contents"], "귀여운 캐릭터!")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(all_search.status_code, 200)

    def test_search_user_notice_title(self):
        self.client.force_authenticate(user=self.watcher)

        type = "title"
        keyword = "개강파티"
        title_search = self.client.get(
            f"/api/v1/users/me/notices/search/?type={type}&q={keyword}"
        )
        data = title_search.json()["results"]
        self.assertEqual(len(data), 1)

        result_1 = data[0]
        self.assertEqual(result_1["title"], "와플스튜디오 개강파티")
        self.assertEqual(result_1["contents"], "3월 12일 저녁 7시")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(title_search.status_code, 200)

    def test_search_user_notice_contents(self):
        self.client.force_authenticate(user=self.watcher)

        type = "contents"
        keyword = "귀여운"
        contents_search = self.client.get(
            f"/api/v1/users/me/notices/search/?type={type}&q={keyword}"
        )
        data = contents_search.json()["results"]
        self.assertEqual(len(data), 1)

        result_1 = data[0]
        self.assertEqual(result_1["title"], "와플스튜디오 로고 캐릭터 선정")
        self.assertEqual(result_1["contents"], "귀여운 캐릭터!")
        self.assertEqual(result_1["channel"], self.channel_id)
        self.assertEqual(result_1["writer"], self.manager.id)

        self.assertEqual(contents_search.status_code, 200)

    def test_search_user_notice_less_than_two_letters(self):
        self.client.force_authenticate(user=self.watcher)

        type = "all"
        keyword = "와"
        less_than_two_search = self.client.get(
            f"/api/v1/users/me/notices/search/?type={type}&q={keyword}"
        )
        self.assertEqual(less_than_two_search.status_code, 400)

    def test_search_user_notice_invalid_keyword(self):
        self.client.force_authenticate(user=self.watcher)

        type = "all"
        keyword = "검색되지않는단어"
        not_search = self.client.get(
            f"/api/v1/users/me/notices/search/?type={type}&q={keyword}"
        )
        self.assertEqual(not_search.status_code, 400)
