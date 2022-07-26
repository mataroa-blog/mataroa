from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from main import models


class WebringAnonGetTestCase(TestCase):
    def test_webring_get_naked(self):
        response = self.client.get(reverse("webring"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webring Integration")

    def test_webring_get_subdomain(self):
        self.user = models.User.objects.create(username="alice")
        response = self.client.get(
            reverse("webring"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webring Integration")


class WebringAnonPostTestCase(TestCase):
    def test_webring_post_naked(self):
        response = self.client.post(reverse("webring"))
        self.assertEqual(response.status_code, 302)

    def test_webring_post_subdomain(self):
        self.user = models.User.objects.create(username="alice")
        response = self.client.post(
            reverse("webring"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 302)


class WebringGetTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_webring_get_naked(self):
        response = self.client.get(reverse("webring"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webring Integration")
        self.assertContains(response, "Webring name")

    def test_webring_get_subdomain(self):
        response = self.client.get(
            reverse("webring"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webring Integration")
        self.assertContains(response, "Webring name")


class WebringPostTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_webring_post_naked(self):
        data = {
            "webring_name": "Bloggers Webring",
            "webring_url": "http://our-webring-for-bloggers.ring",
            "webring_prev_url": "http://prev-blog.ring",
            "webring_next_url": "http://next-blog.ring",
        }
        response = self.client.post(
            reverse("webring"),
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            models.User.objects.get(username="alice").webring_name, data["webring_name"]
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_url, data["webring_url"]
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_prev_url,
            data["webring_prev_url"],
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_next_url,
            data["webring_next_url"],
        )

    def test_webring_post_subdomain(self):
        data = {
            "webring_name": "Bloggers Webring",
            "webring_url": "http://our-webring-for-bloggers.ring",
            "webring_prev_url": "http://prev-blog.ring",
            "webring_next_url": "http://next-blog.ring",
        }
        response = self.client.post(
            reverse("webring"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            models.User.objects.get(username="alice").webring_name, data["webring_name"]
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_url, data["webring_url"]
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_prev_url,
            data["webring_prev_url"],
        )
        self.assertEqual(
            models.User.objects.get(username="alice").webring_next_url,
            data["webring_next_url"],
        )
