from django.test import TestCase
from rest_framework.test import APIClient

from apps.user.models import EmailInfo, User


class EmailTest(TestCase):
    def setUp(self):
        self.info = EmailInfo.of("heka1024")
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testmailuser",
            email="heka1024@snu.ac.kr",
            password="password",
            first_name="first",
            last_name="last",
        )

        self.user_b = User.objects.create_user(
            username="testuser",
            email="wafflestudio@snu.ac.kr",
            password="password",
            first_name="first",
            last_name="last",
        )

    def test_send_mail(self):
        self.assertEqual(EmailInfo.objects.count(), 1)

        send = self.client.post(
            "/api/v1/users/mail/send/", {"email_prefix": "heka1024"}
        )

        self.assertEqual(send.status_code, 200)
        self.assertEqual(EmailInfo.objects.count(), 1)

    def test_send_mail_no_info(self):
        self.info.delete()

        send = self.client.post(
            "/api/v1/users/mail/send/", {"email_prefix": "heka1024"}
        )

        self.assertEqual(send.status_code, 200)
        self.assertEqual(EmailInfo.objects.count(), 1)

    def test_send_mail_verified(self):
        self.assertEqual(EmailInfo.objects.count(), 1)
        self.info.is_verified = True
        self.info.save()

        send = self.client.post(
            "/api/v1/users/mail/send/", {"email_prefix": "heka1024"}
        )
        self.assertEqual(send.status_code, 400)
        self.assertEqual(EmailInfo.objects.count(), 1)

    def test_verify_mail(self):
        self.assertEqual(EmailInfo.objects.count(), 1)

        send = self.client.post(
            "/api/v1/users/mail/verify/",
            {"email_prefix": "heka1024", "code": self.info.verification_code},
        )

        self.assertEqual(send.status_code, 200)
        info = EmailInfo.objects.last()
        self.assertTrue(info.is_verified)

    def test_username_mail(self):
        self.assertEqual(EmailInfo.objects.count(), 1)
        send = self.client.post(
            "/api/v1/users/find/username/", {"email_prefix": "heka1024"}
        )
        self.assertEqual(send.status_code, 200)
        self.assertEqual(EmailInfo.objects.count(), 1)

        send = self.client.post(
            "/api/v1/users/find/username/", {"email_prefix": "mieseung"}
        )
        self.assertEqual(send.status_code, 400)
        self.assertEqual(EmailInfo.objects.count(), 1)

    def test_password_mail(self):
        self.assertEqual(EmailInfo.objects.count(), 1)
        send = self.client.post(
            "/api/v1/users/find/password/",
            {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email_prefix": "heka1024",
            },
        )

        self.assertEqual(send.status_code, 200)
        self.assertEqual(EmailInfo.objects.count(), 1)
        self.assertNotEqual(
            User.objects.get(email="heka1024@snu.ac.kr").password, "password"
        )

        send = self.client.post(
            "/api/v1/users/find/password/", {"email_prefix": "mieseung"}
        )
        self.assertEqual(send.status_code, 400)
        self.assertEqual(EmailInfo.objects.count(), 1)
