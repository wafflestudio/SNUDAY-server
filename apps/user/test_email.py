from django.test import TestCase
from rest_framework.test import APIClient

from apps.user.models import EmailInfo


class EmailTest(TestCase):
    def setUp(self):
        self.info = EmailInfo.of("heka1024")
        self.client = APIClient()

    def test_send_mail(self):
        self.assertEqual(EmailInfo.objects.count(), 1)

        send = self.client.post(
            "/api/v1/users/mail/send/", {"email_prefix": "heka1024"}
        )

        self.assertEqual(send.status_code, 200)
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
