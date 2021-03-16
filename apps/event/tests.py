from django.test import Client, TestCase
from rest_framework import status
from apps.channel.models import Channel
from apps.user.models import User
from .models import Event
import json
from rest_framework.test import APIClient


class EventTest(TestCase):
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

        self.data = {
            "title": "event title",
            "memo": "event memo",
            "has_time": True,
            "start_date": "1998-12-11T00:00:00+09:00",
            "due_date": "2021-03-03T23:51:00+09:00",
        }

        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    def test_create_event(self):
        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            self.data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "event title")
        self.assertEqual(data["memo"], "event memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertEqual(data["start_date"], "1998-12-11T00:00:00+09:00")
        self.assertEqual(data["due_date"], "2021-03-03T23:51:00+09:00")

        self.event_1 = Event.objects.create(
            title="event title",
            memo="event memo",
            channel=self.channel,
            writer=self.manager,
            has_time=False,
        )

        response = self.client.get(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()["results"]

        self.assertEqual(len(data), 2)

        for i in range(2):

            self.assertIn("id", data[i])
            self.assertEqual(data[i]["title"], "event title")
            self.assertEqual(data[i]["memo"], "event memo")
            self.assertEqual(data[i]["channel"], self.channel_id)
            self.assertEqual(data[i]["writer"], self.manager.id)
            self.assertIn("created_at", data[i])
            self.assertIn("updated_at", data[i])

        self.assertEqual(data[1]["start_date"], "1998-12-11T00:00:00+09:00")
        self.assertEqual(data[1]["due_date"], "2021-03-03T23:51:00+09:00")

        self.assertIsNone(data[0]["start_date"])
        self.assertIsNone(data[0]["due_date"])

        response = self.client.get(
            "/api/v1/channels/{}/events/".format(str(self.channel_id + 1)),
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_event_incomplete_request(self):
        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            json.dumps(
                {
                    "memo": "event memo",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 0)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            json.dumps(
                {
                    "memo": "event memo",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 0)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            json.dumps(
                {
                    "title": "event title",
                    "memo": "event memo",
                    "has_time": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 0)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {
                "title": "event title",
                "memo": "event memo",
                "has_time": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        event_id = response.json()["id"]

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_id)
            ),
            {
                "has_time": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Event.objects.count(), 1)

        self.assertFalse(Event.objects.filter(id=event_id).first().has_time)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_id)
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Event.objects.count(), 1)

    def test_no_event(self):
        event_count = Event.objects.count()

        # miss data
        a = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_count)
            )
        )

        self.assertEqual(a.status_code, 400)

        # no channel id
        b = self.client.get(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id + 1), str(event_count)
            )
        )

        self.assertEqual(b.status_code, 400)

        c = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id + 1), str(event_count)
            ),
            {
                "title": "updated title",
            },
            format="json",
        )

        self.assertEqual(c.status_code, 400)

        d = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id + 1), str(event_count)
            )
        )

        self.assertEqual(d.status_code, 400)

        # no event id
        e = self.client.get(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_count + 1)
            )
        )

        self.assertEqual(e.status_code, 404)

        f = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_count + 1)
            )
        )

        self.assertEqual(f.status_code, 400)

        g = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(event_count + 1)
            ),
            {
                "title": "updated title",
            },
            format="json",
        )

        self.assertEqual(g.status_code, 400)


class PublicChannelEventTest(TestCase):
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

        self.data = {
            "title": "event title",
            "memo": "event memo",
            "has_time": True,
            "start_date": "1998-12-11T00:00:00+09:00",
            "due_date": "2021-03-03T23:51:00+09:00",
        }

        self.client = APIClient()

        self.event_1 = Event.objects.create(
            title="event title",
            memo="event memo",
            channel=self.channel,
            writer=self.manager,
            has_time=False,
        )

    def test_manager_patch_event(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            ),
            {"title": "updated title", "memo": "updated memo"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated title")
        self.assertEqual(data["memo"], "updated memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertFalse(data["has_time"])

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
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
        self.assertEqual(data["memo"], "updated memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertFalse(data["has_time"])

    def test_manager_delete_event(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {
                "title": "title will be deleted",
                "memo": "memo will be deleted",
                "has_time": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 2)

        data = response.json()
        delete_event_id = data["id"]

        response = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(delete_event_id)
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(response.data)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

    def test_subscriber_event(self):
        self.client.force_authenticate(user=self.subscriber)
        self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {"title": "title", "memo": "memo", "has_time": False},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            ),
            {"title": "updated title", "memo": "updated memo"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Event.objects.get(id=self.event_1.id)

        self.assertEqual(data.title, "event title")
        self.assertEqual(data.memo, "event memo")

        response = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], self.event_1.id)
        self.assertEqual(data["title"], "event title")
        self.assertEqual(data["memo"], "event memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        response = self.client.get("/api/v1/users/me/events/")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)

        data = data[0]
        self.assertIn("id", data)
        self.assertEqual(data["title"], "event title")
        self.assertEqual(data["memo"], "event memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertFalse(data["has_time"])

        response = self.client.get(
            "/api/v1/users/{}/events/".format(str(self.subscriber.id + 1))
        )

        self.assertEqual(response.status_code, 403)

    def test_watcher_event(self):
        self.client.force_authenticate(user=self.watcher)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {"title": "title", "memo": "memo", "has_time": False},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            ),
            {"title": "updated title", "memo": "updated memo"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Event.objects.get(id=self.event_1.id)

        self.assertEqual(data.title, "event title")
        self.assertEqual(data.memo, "event memo")

        response = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], self.event_1.id)
        self.assertEqual(data["title"], "event title")
        self.assertEqual(data["memo"], "event memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertFalse(data["has_time"])


class PrivateChannelEventTest(TestCase):
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

        self.data = {
            "title": "event title",
            "memo": "event memo",
            "has_time": True,
            "start_date": "1998-12-11T00:00:00+09:00",
            "due_date": "2021-03-03T23:51:00+09:00",
        }

        self.client = APIClient()

        self.event_1 = Event.objects.create(
            title="event title",
            memo="event memo",
            channel=self.channel,
            writer=self.manager,
            has_time=False,
        )

    def test_manager_patch_event(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            ),
            {"title": "updated title", "memo": "updated memo"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "updated title")
        self.assertEqual(data["memo"], "updated memo")
        self.assertEqual(data["channel"], self.channel_id)
        self.assertEqual(data["writer"], self.manager.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_manager_delete_event(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {
                "title": "title will be deleted",
                "memo": "memo will be deleted",
                "has_time": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 2)

        data = response.json()
        delete_event_id = data["id"]

        response = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(delete_event_id)
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(response.data)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

    def test_watcher_event(self):
        self.client.force_authenticate(user=self.watcher)

        response = self.client.post(
            "/api/v1/channels/{}/events/".format(str(self.channel_id)),
            {"title": "title", "memo": "memo", "has_time": False},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.patch(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            ),
            {"title": "updated title", "memo": "updated memo"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        data = Event.objects.get(id=self.event_1.id)

        self.assertEqual(data.title, "event title")
        self.assertEqual(data.memo, "event memo")

        response = self.client.delete(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        event_count = Event.objects.count()
        self.assertEqual(event_count, 1)

        response = self.client.get(
            "/api/v1/channels/{}/events/{}/".format(
                str(self.channel_id), str(self.event_1.id)
            )
        )

        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            "/api/v1/channels/{}/events/".format(str(self.channel_id))
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())

        response = self.client.get("/api/v1/users/me/events/")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 0)

    def test_subscriber_event(self):
        self.client.force_authenticate(user=self.watcher)
        subscribe = self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")
        self.assertEqual(subscribe.status_code, 204)

        self.client.force_authenticate(user=self.manager)
        allow = self.client.post(
            f"/api/v1/channels/{self.channel_id}/awaiters/allow/{self.watcher.id}/"
        )
        self.assertEqual(allow.status_code, 200)

        response = self.client.get(f"/api/v1/channels/{self.channel_id}/events/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"/api/v1/channels/{self.channel_id}/events/{self.event_1.id}/"
        )
        self.assertEqual(response.status_code, 200)


class ParticularDateEventTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@email.com",
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

        self.channel = Channel.objects.create(
            name="wafflestudio",
            description="맛있는 서비스가 탄생하는 곳, 서울대학교 컴퓨터공학부 웹/앱 개발 동아리 와플스튜디오입니다!",
            is_private=False,
        )

        self.channel_2 = Channel.objects.create(
            name="서울대학교 ETL",
            description="서버가 종종 터져요",
            is_private=False,
        )

        self.channel_id = self.channel.id
        self.channel_2_id = self.channel_2.id

        self.channel.managers.set([self.manager])
        self.channel_2.managers.set([self.manager])

        self.client = APIClient()

        self.event_1 = Event.objects.create(
            title="event title",
            memo="event memo",
            channel=self.channel,
            writer=self.manager,
            has_time=False,
        )

        self.event_2 = Event.objects.create(
            title="event title2",
            memo="event memo2",
            channel=self.channel,
            writer=self.manager,
            has_time=True,
            start_date="1998-12-11T00:00:00+09:00",
            due_date="2021-12-11T00:00:00+09:00",
        )

        self.event_3 = Event.objects.create(
            title="event title3",
            memo="event memo3",
            channel=self.channel,
            writer=self.manager,
            has_time=True,
            start_date="2021-03-15T00:00:00+09:00",
            due_date="2021-03-15T02:00:00+09:00",
        )

        self.event_4 = Event.objects.create(
            title="event title4",
            memo="event memo4",
            channel=self.channel,
            writer=self.manager,
            has_time=True,
            start_date="2021-03-15T00:00:00+09:00",
            due_date="2021-03-16T00:00:00+09:00",
        )

        self.event_5 = Event.objects.create(
            title="서버가 터짐",
            memo="등록금 환불해줘야할듯",
            channel=self.channel_2,
            writer=self.manager,
            has_time=True,
            start_date="2021-03-15T00:00:00+09:00",
            due_date="2021-03-17T00:00:00+09:00",
        )

    def test_subscribing_channel_events(self):
        self.client.force_authenticate(user=self.b)

        subscribe = self.client.post(f"/api/v1/channels/{self.channel_id}/subscribe/")

        date_1 = "2021-03-15"
        date_1_result = self.client.get(f"/api/v1/users/me/events/?date={date_1}")

        data = date_1_result.json()
        self.assertEqual(date_1_result.status_code, 200)
        self.assertEqual(len(data), 3)

        event_result_1 = data[2]
        self.assertEqual(event_result_1["title"], "event title4")
        self.assertEqual(event_result_1["memo"], "event memo4")

        subscribe_2 = self.client.post(
            f"/api/v1/channels/{self.channel_2_id}/subscribe/"
        )

        date_2 = "2021-03-16"
        date_2_result = self.client.get(f"/api/v1/users/me/events/?date={date_2}")
        data_2 = date_2_result.json()
        self.assertEqual(date_2_result.status_code, 200)
        self.assertEqual(len(data_2), 2)
        event_result_2 = data_2[1]
        self.assertEqual(event_result_2["title"], "서버가 터짐")
        self.assertEqual(event_result_2["memo"], "등록금 환불해줘야할듯")

    def test_channel_events(self):
        self.client.force_authenticate(user=self.b)

        date = "2021-03-15"
        date_result = self.client.get(
            f"/api/v1/channels/{self.channel_id}/events/?date={date}"
        )
        self.assertEqual(date_result.status_code, 200)

        data = date_result.json()["results"]
        self.assertEqual(len(data), 3)
        event_result = data[0]
        self.assertEqual(event_result["title"], "event title4")
        self.assertEqual(event_result["memo"], "event memo4")

        date_2 = "2021-03-20"
        no_result = self.client.get(
            f"/api/v1/channels/{self.channel_2_id}/events/?date={date_2}"
        )
        self.assertEqual(no_result.status_code, 200)
        self.assertEqual(len(no_result.json()["results"]), 0)
