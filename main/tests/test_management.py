from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from main import models
from main.management.commands import process_notifications


class EnqueueNotificationsTest(TestCase):
    """
    Test that the enqueue_notifications management command, creates NotificationRecords
    to the blog_user subscribers.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@wonderland.com", notifications_on=True
        )

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        models.Post.objects.create(owner=self.user, **post_data)

        post_data = {
            "title": "Today post",
            "slug": "today-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 2)),
        }
        models.Post.objects.create(owner=self.user, **post_data)

        # as inactive, it should be ignored by the enqueue functionality
        self.notification_inactive = models.Notification.objects.create(
            blog_user=self.user,
            email="inactive@example.com",
            is_active=False,
        )

        self.notification = models.Notification.objects.create(
            blog_user=self.user, email="s@example.com"
        )

    def test_command(self):
        output = StringIO()

        with patch.object(timezone, "now", return_value=datetime(2020, 1, 2, 9, 00)):
            call_command("enqueue_notifications", stdout=output)

        # notification records
        self.assertEqual(len(models.NotificationRecord.objects.all()), 1)
        self.assertEqual(
            models.NotificationRecord.objects.first().notification.email,
            self.notification.email,
        )
        self.assertEqual(
            models.NotificationRecord.objects.first().post.title, "Today post"
        )
        self.assertIsNone(models.NotificationRecord.objects.first().sent_at)

        # logging
        self.assertIn("Enqueuing notifications started.", output.getvalue())
        self.assertIn(
            "Adding notification record for 'Today post' to 's@example.com'",
            output.getvalue(),
        )
        self.assertIn("Enqueuing complete for 'Today post'", output.getvalue())
        self.assertIn("Enqueuing finished.", output.getvalue())

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()


class ProcessNotificationsTest(TestCase):
    """
    Test process_notifications sends emails to the subscibers of the
    NotificationRecords that exist.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@wonderland.com", notifications_on=True
        )

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        self.post_yesterday = models.Post.objects.create(owner=self.user, **post_data)

        post_data = {
            "title": "Today post",
            "slug": "today-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 2)),
        }
        self.post_today = models.Post.objects.create(owner=self.user, **post_data)

        self.notification = models.Notification.objects.create(
            blog_user=self.user, email="zf@sirodoht.com"
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post_yesterday,
            sent_at=None,
        )

    def test_mail_backend(self):
        connection = process_notifications.get_mail_connection()
        self.assertEqual(connection.host, settings.EMAIL_HOST_BROADCASTS)

    def test_command(self):
        output = StringIO()

        with patch.object(
            timezone, "now", return_value=datetime(2020, 1, 2, 13, 00)
        ), patch.object(
            # Django default test runner overrides SMTP EmailBackend with locmem,
            # but because we re-import the SMTP backend in
            # process_notifications.get_mail_connection, we need to mock it here too.
            process_notifications,
            "get_mail_connection",
            return_value=mail.get_connection(
                "django.core.mail.backends.locmem.EmailBackend"
            ),
        ):
            call_command("process_notifications", stdout=output)

        # notification record
        self.assertEqual(len(models.NotificationRecord.objects.all()), 1)
        self.assertEqual(
            models.NotificationRecord.objects.first().notification.email,
            self.notification.email,
        )
        self.assertEqual(
            models.NotificationRecord.objects.first().post.title, "Yesterday post"
        )
        self.assertIsNotNone(models.NotificationRecord.objects.first().sent_at.date())

        # logging
        self.assertIn("Processing notifications.", output.getvalue())
        self.assertIn("Broadcast sent. Total 1 emails.", output.getvalue())
        self.assertNotIn("Today post", output.getvalue())

        # email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "alice new post publication: Yesterday post"
        )
        self.assertIn("To unsubscribe", mail.outbox[0].body)

        # email headers
        self.assertEqual(mail.outbox[0].to, [self.notification.email])
        self.assertEqual(mail.outbox[0].reply_to, [self.user.email])
        self.assertEqual(mail.outbox[0].from_email, settings.NOTIFICATIONS_FROM_EMAIL)

        self.assertEqual(
            mail.outbox[0].extra_headers["X-PM-Message-Stream"], "newsletters"
        )
        self.assertIn(
            "/newsletter/unsubscribe/",
            mail.outbox[0].extra_headers["List-Unsubscribe"],
        )
        self.assertEqual(
            mail.outbox[0].extra_headers["List-Unsubscribe-Post"],
            "List-Unsubscribe=One-Click",
        )

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()


class NonActiveNotificationsTest(TestCase):
    """
    Test process_notifications does not send emails to is_active=False
    subscibers.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@wonderland.com", notifications_on=True
        )

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        self.post_yesterday = models.Post.objects.create(owner=self.user, **post_data)

        post_data = {
            "title": "Today post",
            "slug": "today-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 2)),
        }
        self.post_today = models.Post.objects.create(owner=self.user, **post_data)

        self.notification = models.Notification.objects.create(
            blog_user=self.user, email="zf@sirodoht.com"
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post_yesterday,
            sent_at=None,
        )

    def test_mail_backend(self):
        connection = process_notifications.get_mail_connection()
        self.assertEqual(connection.host, settings.EMAIL_HOST_BROADCASTS)

    def test_command(self):
        output = StringIO()

        with patch.object(
            timezone, "now", return_value=datetime(2020, 1, 2, 13, 00)
        ), patch.object(
            # Django default test runner overrides SMTP EmailBackend with locmem,
            # but because we re-import the SMTP backend in
            # process_notifications.get_mail_connection, we need to mock it here too.
            process_notifications,
            "get_mail_connection",
            return_value=mail.get_connection(
                "django.core.mail.backends.locmem.EmailBackend"
            ),
        ):
            call_command("process_notifications", stdout=output)

        # notification record
        self.assertEqual(len(models.NotificationRecord.objects.all()), 1)
        self.assertEqual(
            models.NotificationRecord.objects.first().notification.email,
            self.notification.email,
        )
        self.assertEqual(
            models.NotificationRecord.objects.first().post.title, "Yesterday post"
        )
        self.assertIsNotNone(models.NotificationRecord.objects.first().sent_at.date())

        # logging
        self.assertIn("Processing notifications.", output.getvalue())
        self.assertIn("Broadcast sent. Total 1 emails.", output.getvalue())
        self.assertNotIn("Today post", output.getvalue())

        # email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "alice new post publication: Yesterday post"
        )
        self.assertIn("To unsubscribe", mail.outbox[0].body)

        # email headers
        self.assertEqual(mail.outbox[0].to, [self.notification.email])
        self.assertEqual(mail.outbox[0].reply_to, [self.user.email])
        self.assertEqual(mail.outbox[0].from_email, settings.NOTIFICATIONS_FROM_EMAIL)

        self.assertEqual(
            mail.outbox[0].extra_headers["X-PM-Message-Stream"], "newsletters"
        )
        self.assertIn(
            "/newsletter/unsubscribe/",
            mail.outbox[0].extra_headers["List-Unsubscribe"],
        )
        self.assertEqual(
            mail.outbox[0].extra_headers["List-Unsubscribe-Post"],
            "List-Unsubscribe=One-Click",
        )

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()
