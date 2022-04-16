from django.test import TestCase
from django.urls import reverse

from main import models


class APIDocsAnonTestCase(TestCase):
    def test_docs_get(self):
        response = self.client.get(reverse("api_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API")


class APIDocsTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_docs_get(self):
        response = self.client.get(reverse("api_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API")
        self.assertContains(response, self.user.api_key)


class APIPostsAnonTestCase(TestCase):
    def test_posts_anon_get(self):
        response = self.client.get(reverse("api_posts"))
        self.assertEqual(response.status_code, 405)

    def test_posts_anon_post(self):
        response = self.client.post(reverse("api_posts"))
        self.assertEqual(response.status_code, 403)


class APIPostsTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_posts_get(self):
        response = self.client.get(reverse("api_posts"))
        self.assertEqual(response.status_code, 405)

    def test_posts_post_no_auth(self):
        response = self.client.post(reverse("api_posts"))
        self.assertEqual(response.status_code, 403)

    def test_posts_post_bad_auth(self):
        response = self.client.post(
            reverse("api_posts"), HTTP_AUTHORIZATION=f"Nearer {self.user.api_key}"
        )
        self.assertEqual(response.status_code, 400)

    def test_posts_post_wrong_auth(self):
        response = self.client.post(
            reverse("api_posts"),
            HTTP_AUTHORIZATION="Bearer 12345678901234567890123456789012",
        )
        self.assertEqual(response.status_code, 403)

    def test_posts_post_good_auth(self):
        response = self.client.post(
            reverse("api_posts"), HTTP_AUTHORIZATION=f"Bearer {self.user.api_key}"
        )
        self.assertEqual(response.status_code, 400)

    def test_posts_post_no_title(self):
        self.data = {
            "body": "This is my post with no title key",
        }
        response = self.client.post(
            reverse("api_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.user.api_key}",
            content_type="application/json",
            data=self.data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(models.Post.objects.all().count(), 0)

    def test_posts_post_no_body(self):
        self.data = {
            "title": "First Post no body key",
        }
        response = self.client.post(
            reverse("api_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.user.api_key}",
            content_type="application/json",
            data=self.data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(models.Post.objects.all().count(), 0)

    def test_posts_post(self):
        self.data = {
            "title": "First Post",
            "body": "## Welcome\n\nThis is my first sentence.",
        }
        response = self.client.post(
            reverse("api_posts"),
            HTTP_AUTHORIZATION=f"Bearer {self.user.api_key}",
            content_type="application/json",
            data=self.data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Post.objects.all().count(), 1)
        self.assertEqual(models.Post.objects.all().first().title, self.data["title"])
        self.assertEqual(models.Post.objects.all().first().body, self.data["body"])
        models.Post.objects.all().first().delete()
