from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main import models
from mataroa import settings


class SitemapFormatTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")

    def test_sitemap_valid(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<?xml version="1.0" encoding="UTF-8"?>')
        self.assertContains(
            response,
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        )


class SitemapIndexTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")

    def test_index_exists(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertContains(
            response, f"//{self.user.username}.{settings.CANONICAL_HOST}/</loc>"
        )


class SitemapPostTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "slug": "new-post",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_exists(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</loc>",
        )


class SitemapFuturePostTestCase(TestCase):
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
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</loc>",
        )


class SitemapPostDraftTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {"slug": "new-draft", "published_at": None}
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_draft_hidden(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/blog/{self.data['slug']}/</loc>",
        )


class SitemapPageTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "slug": "new-page",
        }
        self.page = models.Page.objects.create(owner=self.user, **self.data)

    def test_page_exists(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/{self.data['slug']}/</loc>",
        )


class SitemapHiddenPageTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {"slug": "new-hidden-page", "is_hidden": True}
        self.page = models.Page.objects.create(owner=self.user, **self.data)

    def test_hidden_page_hidden(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        # do not include <loc> so the assertion matches all protocols
        self.assertNotContains(
            response,
            f"//{self.user.username}.{settings.CANONICAL_HOST}/{self.data['slug']}/</loc>",
        )


class SitemapCustomDomainTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(
            username="alice", custom_domain="blog.test"
        )
        self.client.force_login(self.user)
        self.data = {
            "slug": "new-post",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_custom_baseurl(self):
        response = self.client.get(
            reverse("sitemap"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.custom_domain,
        )
        self.assertContains(response, f"//blog.test/blog/{self.data['slug']}/</loc>")
