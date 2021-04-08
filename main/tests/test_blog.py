from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main import models


class IndexTestCase(TestCase):
    """ Test canonical mataroa.blog works."""

    def test_index(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mataroa")


class BlogIndexTestCase(TestCase):
    """Test blog index works for logged in."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_index(self):
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.data["title"])


class BlogIndexAnonTestCase(TestCase):
    """Test blog index works for anon."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.save()
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_index_non(self):
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.data["title"])


class BlogIndexRedirTestCase(TestCase):
    """Test logged in user is redirected from canonical to blog index."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_index_redir(self):
        response = self.client.get(reverse("blog_index"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            f"{self.user.username}.{settings.CANONICAL_HOST}" in response.url
        )


class BlogRetiredRedirTestCase(TestCase):
    """
    Test anon user is redirected to redirect_domain,
    when redirect_domain exists without protocol prefix.
    """

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.redirect_domain = "example.com"
        self.user.save()
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_retired_redir(self):
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(f"//{self.user.redirect_domain}/", response.url)


class BlogRetiredRedirProtocolTestCase(TestCase):
    """
    Test anon user is redirected to redirect_domain,
    when redirect_domain exists with protocol prefix http.
    """

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.redirect_domain = "http://example.com"
        self.user.save()
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_retired_redir(self):
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.redirect_domain + "/", response.url)


class BlogImportTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.blog_title = "Blog of Alice"
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_blog_import(self):
        filename = "main/tests/testdata/lorem.md"
        with open(filename) as fp:
            self.client.post(reverse("blog_import"), {"file": fp})
            self.assertTrue(models.Post.objects.filter(title="lorem.md").exists())
            self.assertTrue(
                "Curabitur pretium tincidunt lacus"
                in models.Post.objects.get(title="lorem.md").body
            )


class BlogExportMarkdownTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_export(self):
        response = self.client.post(reverse("blog_export_markdown"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertContains(response, "export-markdown".encode("utf-8"))
        self.assertContains(response, self.data["slug"].encode("utf-8"))


class BlogExportZolaTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_export(self):
        response = self.client.post(reverse("blog_export_zola"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertContains(response, "export-zola".encode("utf-8"))
        self.assertContains(response, self.data["slug"].encode("utf-8"))


class BlogExportHugoTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_export(self):
        response = self.client.post(reverse("blog_export_hugo"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertContains(response, "export-hugo".encode("utf-8"))
        self.assertContains(response, self.data["slug"].encode("utf-8"))


class RSSFeedTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
            "published_at": timezone.now(),
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_rss_feed(self):
        response = self.client.get(
            reverse("rss_feed"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertContains(response, self.data["title"])
        self.assertContains(response, self.data["slug"])
        self.assertContains(response, self.data["body"])


class RSSFeedDraftsTestCase(TestCase):
    """Tests draft posts do not appear in the RSS feed."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.post_published = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
            "published_at": timezone.now(),
        }
        models.Post.objects.create(owner=self.user, **self.post_published)
        self.post_draft = {
            "title": "Hidden post",
            "slug": "hidden-post",
            "body": "Hidden sentence.",
            "published_at": None,
        }
        models.Post.objects.create(owner=self.user, **self.post_draft)

    def test_rss_feed(self):
        response = self.client.get(
            reverse("rss_feed"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertContains(response, self.post_published["title"])
        self.assertContains(response, self.post_published["slug"])
        self.assertContains(response, self.post_published["body"])
        self.assertNotContains(response, self.post_draft["title"])
        self.assertNotContains(response, self.post_draft["slug"])
        self.assertNotContains(response, self.post_draft["body"])


class BlogNotificationListTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )

    def test_subscibers_list(self):
        response = self.client.get(reverse("notification_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b"s@example.com")


class BlogNotificationSubscribeTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.notifications_on = True
        self.user.save()

    def test_blog_subscribe(self):
        response = self.client.post(
            reverse("notification_subscribe"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
            data={"email": "s@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.Notification.objects.filter(
                blog_user=self.user, email="s@example.com", is_active=True
            ).exists()
        )


class BlogNotificationUnsubscribeTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )

    def test_blog_unsubscribe(self):
        response = self.client.post(
            reverse("notification_unsubscribe"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
            data={"email": "s@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            models.Notification.objects.get(email="s@example.com").is_active
        )


class BlogNotificationUnsubscribeKeyTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )

    def test_blog_unsubscribe_key(self):
        response = self.client.get(
            reverse(
                "notification_unsubscribe_key",
                args=(self.notification.unsubscribe_key,),
            ),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            models.Notification.objects.filter(
                email="s@example.com", is_active=False
            ).exists()
        )


class BlogNotificationResubscribeTestCase(TestCase):
    """Test one can subscribe after having unsubscribed."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.notifications_on = True
        self.user.save()

        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
            is_active=False,
        )

    def test_blog_resubscribe(self):
        response = self.client.post(
            reverse("notification_subscribe"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
            data={"email": "s@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.Notification.objects.filter(
                email="s@example.com", is_active=True
            ).exists()
        )


class BlogNotificationUnsubscriberNotShownTestCase(TestCase):
    """Test someone who unsubscribes does not appear on list."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.notifications_on = True
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

        self.notification_active = models.Notification.objects.create(
            blog_user=self.user,
            email="active@example.com",
            is_active=True,
        )
        self.notification_inactive = models.Notification.objects.create(
            blog_user=self.user,
            email="inactive@example.com",
            is_active=False,
        )

    def test_blog_unsubscribed_not_shown(self):
        response = self.client.get(
            reverse("notification_list"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.notification_active.email)
        self.assertNotContains(response, self.notification_inactive.email)


class BlogNotificationRecordListTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at="2020-01-01",
        )

    def test_notificationrecord_list(self):
        response = self.client.get(reverse("notificationrecord_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b"s@example.com")
        self.assertContains(response, b"2020-01-01")


class BlogNotificationRecordConfirmDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at=None,
        )

    def test_notificationrecord_delete(self):
        response = self.client.get(
            reverse("notificationrecord_delete", args=(self.notificationrecord.id,))
        )
        self.assertEqual(response.status_code, 200)


class BlogNotificationRecordDeleteAnonTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at=None,
        )

    def test_notificationrecord_delete(self):
        response = self.client.post(
            reverse("notificationrecord_delete", args=(self.notificationrecord.id,))
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            models.NotificationRecord.objects.filter(
                id=self.notificationrecord.id
            ).exists()
        )


class BlogNotificationRecordDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at=None,
        )

    def test_notificationrecord_delete(self):
        self.client.post(
            reverse("notificationrecord_delete", args=(self.notificationrecord.id,))
        )
        self.assertFalse(
            models.NotificationRecord.objects.filter(
                post=self.notificationrecord.post
            ).exists()
        )


class BlogNotificationRecordDeletePastTestCase(TestCase):
    """
    Test that one cannot delete a notification record that has a sent_at date,
    which means it has already been sent.
    """

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.notification = models.Notification.objects.create(
            blog_user=self.user,
            email="s@example.com",
        )
        self.notificationrecord = models.NotificationRecord.objects.create(
            notification=self.notification,
            post=self.post,
            sent_at="2000-01-01",
        )

    def test_notificationrecord_delete(self):
        response = self.client.post(
            reverse("notificationrecord_delete", args=(self.notificationrecord.id,))
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            models.NotificationRecord.objects.filter(
                id=self.notificationrecord.id
            ).exists()
        )
