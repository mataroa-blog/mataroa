from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from main import models
from main.management.commands import mail_exports, process_notifications


class EnqueueNotificationsTest(TestCase):
    """
    Test that the enqueue_notifications management command, creates NotificationRecords
    to the blog_user subscribers.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@mataroa.blog", notifications_on=True
        )

        post_data = {
            "title": "Old post",
            "slug": "old-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2019, 1, 2)),
        }
        models.Post.objects.create(owner=self.user, **post_data)

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        models.Post.objects.create(owner=self.user, **post_data)

        # as inactive, it should be ignored by the enqueue functionality
        models.Notification.objects.create(
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
            models.NotificationRecord.objects.first().post.title, "Yesterday post"
        )
        self.assertIsNone(models.NotificationRecord.objects.first().sent_at)

        # logging
        self.assertIn("Enqueuing notifications started.", output.getvalue())
        self.assertIn(
            "Adding notification record for 'Yesterday post' to 's@example.com'",
            output.getvalue(),
        )
        self.assertIn("Enqueuing complete for 'Yesterday post'", output.getvalue())
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
            username="alice", email="alice@mataroa.blog", notifications_on=True
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

        # notification records
        self.notificationrecord_yesterday = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post_yesterday,
            sent_at=None,
        )
        self.notificationrecord_today = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post_today,
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

        # notification records
        records = models.NotificationRecord.objects.all()
        self.assertEqual(len(records), 2)

        # notification record for yesterday's post
        self.assertEqual(
            records.filter(sent_at__isnull=False).first().notification.email,
            self.notificationrecord_today.notification.email,
        )
        self.assertEqual(
            records.filter(sent_at__isnull=False).first().post.title, "Yesterday post"
        )

        # notification record for today's post
        records = models.NotificationRecord.objects.all()
        self.assertEqual(
            records.filter(sent_at__isnull=True).first().notification.email,
            self.notificationrecord_today.notification.email,
        )
        self.assertEqual(
            records.filter(sent_at__isnull=True).first().post.title, "Today post"
        )

        # logging
        self.assertIn("Processing notifications.", output.getvalue())
        self.assertIn("Broadcast sent. Total 1 emails.", output.getvalue())
        self.assertIn(
            "Logging record for 'Yesterday post' to 'zf@sirodoht.com'",
            output.getvalue(),
        )
        self.assertIn(
            "Skip as pub date is not yesterday: 'Today post' for 'zf@sirodoht.com'.",
            output.getvalue(),
        )

        # email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Yesterday post")
        self.assertIn("Unsubscribe", mail.outbox[0].body)

        # email headers
        self.assertEqual(mail.outbox[0].to, [self.notification.email])
        self.assertEqual(mail.outbox[0].reply_to, [self.user.email])
        self.assertEqual(
            mail.outbox[0].from_email,
            f"{self.user.username} <{self.user.username}@{settings.EMAIL_FROM_HOST}>",
        )

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


class ProcessNotificationsCanceledTest(TestCase):
    """
    Test process_notifications does not send canceled notification record emails.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@mataroa.blog", notifications_on=True
        )

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        self.post = models.Post.objects.create(owner=self.user, **post_data)

        self.notification = models.Notification.objects.create(
            blog_user=self.user, email="zf@sirodoht.com"
        )

        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at=None,
            is_canceled=True,
        )

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

        # notification records
        records = models.NotificationRecord.objects.all()
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records.filter(sent_at__isnull=True).first().notification.email,
            self.notificationrecord.notification.email,
        )
        self.assertEqual(
            records.filter(sent_at__isnull=True).first().post.title, "Yesterday post"
        )

        # logging
        self.assertIn("Processing notifications.", output.getvalue())
        self.assertIn(
            "Skip as record is canceled: 'Yesterday post' for 'zf@sirodoht.com'.",
            output.getvalue(),
        )
        self.assertIn("Broadcast sent. Total 0 emails.", output.getvalue())

        # email
        self.assertEqual(len(mail.outbox), 0)

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()


class ProcessNotificationsUnpublishedTest(TestCase):
    """
    Test process_notifications deletes unpublished notification record.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@mataroa.blog", notifications_on=True
        )

        post_data = {
            "title": "Yesterday post",
            "slug": "yesterday-post",
            "body": "Content sentence.",
            "published_at": None,
        }
        self.post = models.Post.objects.create(owner=self.user, **post_data)

        self.notification = models.Notification.objects.create(
            blog_user=self.user, email="zf@sirodoht.com"
        )

        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at=None,
            is_canceled=False,
        )

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

        # notification records
        records = models.NotificationRecord.objects.all()
        self.assertEqual(len(records), 0)

        # logging
        self.assertIn("Processing notifications.", output.getvalue())
        self.assertIn(
            "Delete as post is now a draft: 'Yesterday post' for 'zf@sirodoht.com'.",
            output.getvalue(),
        )
        self.assertIn("Broadcast sent. Total 0 emails.", output.getvalue())

        # email
        self.assertEqual(len(mail.outbox), 0)

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()


class MailExportsTest(TestCase):
    """
    Test mail_export sends emails to users with `mail_export_on` enabled.
    """

    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", email="alice@mataroa.blog", mail_export_on=True
        )

        post_data = {
            "title": "A post",
            "slug": "a-post",
            "body": "Content sentence.",
            "published_at": timezone.make_aware(datetime(2020, 1, 1)),
        }
        self.post_a = models.Post.objects.create(owner=self.user, **post_data)

        post_data = {
            "title": "Second post",
            "slug": "second-post",
            "body": "Content sentence two.",
            "published_at": timezone.make_aware(datetime(2020, 1, 2)),
        }
        self.post_b = models.Post.objects.create(owner=self.user, **post_data)

    def test_mail_backend(self):
        connection = mail_exports.get_mail_connection()
        self.assertEqual(connection.host, settings.EMAIL_HOST_BROADCASTS)

    def test_command(self):
        output = StringIO()

        with patch.object(
            timezone, "now", return_value=datetime(2020, 1, 1, 00, 00)
        ), patch.object(
            # Django default test runner overrides SMTP EmailBackend with locmem,
            # but because we re-import the SMTP backend in
            # process_notifications.get_mail_connection, we need to mock it here too.
            mail_exports,
            "get_mail_connection",
            return_value=mail.get_connection(
                "django.core.mail.backends.locmem.EmailBackend"
            ),
        ):
            call_command("mail_exports", stdout=output)

        # export records
        records = models.ExportRecord.objects.all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].user, self.user)
        self.assertIn("export-markdown-", records[0].name)

        # logging
        self.assertIn("Processing email exports.", output.getvalue())
        self.assertIn(f"Processing user {self.user.username}.", output.getvalue())
        self.assertIn(f"Export sent to {self.user.username}.", output.getvalue())
        self.assertIn(
            f"Logging export record for '{records[0].name}'.", output.getvalue()
        )
        self.assertIn("Emailing all exports complete.", output.getvalue())

        # email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Mataroa export", mail.outbox[0].subject)
        self.assertIn("Stop receiving exports", mail.outbox[0].body)

        # email headers
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_FROM_EMAIL,
        )

        self.assertEqual(mail.outbox[0].extra_headers["X-PM-Message-Stream"], "exports")
        self.assertIn(
            "/export/unsubscribe/",
            mail.outbox[0].extra_headers["List-Unsubscribe"],
        )
        self.assertEqual(
            mail.outbox[0].extra_headers["List-Unsubscribe-Post"],
            "List-Unsubscribe=One-Click",
        )

    def tearDown(self):
        models.User.objects.all().delete()
        models.Post.objects.all().delete()
