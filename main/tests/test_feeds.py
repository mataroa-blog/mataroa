from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main import models
from mataroa import settings


class RSSFeedTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
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
        self.assertContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</link>",
        )


class RSSFeedDraftsTestCase(TestCase):
    """Tests draft posts do not appear in the RSS feed."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
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
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.post_draft['slug']}/</link>",
        )


class RSSFeedFuturePostTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "New Future Post",
            "slug": "new-future-post",
            "body": "future post body",
            "published_at": timezone.now() + timedelta(1),
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_future_post_hidden(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertNotContains(response, self.data["title"])
        self.assertNotContains(response, self.data["slug"])
        self.assertNotContains(response, self.data["body"])
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</link>",
        )


class RSSFeedFormatTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", blog_title="test title", blog_byline="test about text"
        )

    def test_feed_valid(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<?xml version="1.0" encoding="utf-8"?>')
        self.assertContains(
            response,
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        )
        self.assertContains(response, f"<title>{self.user.blog_title}</title>")
        self.assertContains(
            response, f"<description>{self.user.blog_byline}</description>"
        )
