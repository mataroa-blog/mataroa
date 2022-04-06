from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main import models
from mataroa import settings


class RssFeedFormatTestCase(TestCase):
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
        self.assertContains(
            response,
            '<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        )
        self.assertContains(response, f"<title>{self.user.blog_title}</title>")
        self.assertContains(
            response, f"<description>{self.user.blog_byline}</description>"
        )


class RssFeedPostTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {"slug": "new-post"}
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_exists(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # Do not include <link> so the assertion matches all protocols
        self.assertContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</link>",
        )


class RssFeedFuturePostTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "slug": "new-future-post",
            "published_at": timezone.now() + timedelta(1),
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_future_post_hidden(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # Do not include <link> so the assertion matches all protocols
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</link>",
        )


class RssFeedPostDraftTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {"slug": "new-draft", "published_at": None}
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_draft_hidden(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # Do not include <link> so the assertion matches all protocols
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</link>",
        )
