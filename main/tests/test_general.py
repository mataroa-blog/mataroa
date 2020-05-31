from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from main import models


class IndexTestCase(TestCase):
    def test_index(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)


class BlogExportTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_blog_export(self):
        response = self.client.get(reverse("blog_export"))
        self.assertEqual(response.status_code, 200)


class RSSFeedTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
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
