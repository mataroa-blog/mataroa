from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from main import models


class ModAnonTestCase(TestCase):
    def test_mod_users_get(self):
        response = self.client.get(reverse("mod_users_premium"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_grandfather"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_staff"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_active"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_active_nonnew"))
        self.assertEqual(response.status_code, 404)

    def test_mod_users_post(self):
        response = self.client.post(reverse("mod_users_premium"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_users_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_users_grandfather"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_users_staff"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_users_active"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_users_active_nonnew"))
        self.assertEqual(response.status_code, 404)

    def test_mod_posts_get(self):
        response = self.client.get(reverse("mod_posts_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_posts_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_posts_post(self):
        response = self.client.post(reverse("mod_posts_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_posts_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_pages_get(self):
        response = self.client.get(reverse("mod_pages_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_pages_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_pages_post(self):
        response = self.client.post(reverse("mod_pages_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("mod_pages_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_comments_get(self):
        response = self.client.get(reverse("mod_comments"))
        self.assertEqual(response.status_code, 404)

    def test_mod_comments_post(self):
        response = self.client.post(reverse("mod_comments"))
        self.assertEqual(response.status_code, 404)


class ModNonadminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_mod_users_nonadmin(self):
        response = self.client.get(reverse("mod_users_premium"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_grandfather"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_staff"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_active"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_users_active_nonnew"))
        self.assertEqual(response.status_code, 404)

    def test_mod_posts_nonadmin(self):
        response = self.client.get(reverse("mod_posts_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_posts_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_pages_nonadmin(self):
        response = self.client.get(reverse("mod_pages_new"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("mod_pages_recently"))
        self.assertEqual(response.status_code, 404)

    def test_mod_comments_nonadmin(self):
        response = self.client.get(reverse("mod_comments"))
        self.assertEqual(response.status_code, 404)


class ModAdminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice", is_superuser=True)
        self.client.force_login(self.user)

    def test_mod_users_admin(self):
        response = self.client.get(reverse("mod_users_premium"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_users_new"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_users_grandfather"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_users_staff"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_users_active"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_users_active_nonnew"))
        self.assertEqual(response.status_code, 200)

    def test_mod_posts_admin(self):
        response = self.client.get(reverse("mod_posts_new"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_posts_recently"))
        self.assertEqual(response.status_code, 200)

    def test_mod_pages_admin(self):
        response = self.client.get(reverse("mod_pages_new"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("mod_pages_recently"))
        self.assertEqual(response.status_code, 200)

    def test_mod_comments_admin(self):
        response = self.client.get(reverse("mod_comments"))
        self.assertEqual(response.status_code, 200)


class ModCommentsTestCase(TestCase):
    def setUp(self):
        self.admin = models.User.objects.create(username="alice", is_superuser=True)
        self.user = models.User.objects.create(username="bob", comments_on=True)
        self.post = models.Post.objects.create(
            owner=self.user,
            title="Welcome post",
            slug="welcome-post",
            body="Content sentence.",
            published_at="2020-02-06",
        )
        self.client.force_login(self.user)

    def test_comment_list(self):
        data = {
            "name": "Jon",
            "email": "jon@wick.com",
            "body": "Comment here.",
        }
        response = self.client.post(
            reverse("comment_create", args=(self.post.slug,)),
            HTTP_HOST=f"{self.user.username}.{settings.CANONICAL_HOST}",
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.Comment.objects.all().count(), 1)
        self.assertEqual(models.Comment.objects.all().first().name, data["name"])
        self.assertEqual(models.Comment.objects.all().first().email, data["email"])
        self.assertEqual(models.Comment.objects.all().first().body, data["body"])
        self.assertEqual(models.Comment.objects.all().first().post, self.post)
        self.assertEqual(models.Comment.objects.all().first().is_approved, False)


class ModExpelWithEmailTestCase(TestCase):
    def setUp(self):
        self.admin = models.User.objects.create(username="alice", is_superuser=True)
        self.user = models.User.objects.create(
            username="bob", email="bob@example.local"
        )
        self.post = models.Post.objects.create(
            owner=self.user,
            title="Welcome post",
            slug="welcome-post",
            body="Content sentence.",
            published_at="2020-02-06",
        )
        self.client.force_login(self.admin)

    def test_expel(self):
        response = self.client.post(reverse("mod_expel", args=(self.user.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(models.User.objects.filter(username="bob").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("You have been expelled from Mataroa", mail.outbox[0].subject)
        self.assertIn(
            "Your blog was considered to be outside our Code of Code Publication",
            mail.outbox[0].body,
        )
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].bcc, [settings.EXPEL_LOG])
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_FROM_EMAIL,
        )


class ModExpelNoEmailTestCase(TestCase):
    def setUp(self):
        self.admin = models.User.objects.create(username="alice", is_superuser=True)
        self.user = models.User.objects.create(username="bob")
        self.post = models.Post.objects.create(
            owner=self.user,
            title="Welcome post",
            slug="welcome-post",
            body="Content sentence.",
            published_at="2020-02-06",
        )
        self.client.force_login(self.admin)

    def test_expel(self):
        response = self.client.post(reverse("mod_expel", args=(self.user.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(models.User.objects.filter(username="bob").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("bob has been expelled from Mataroa", mail.outbox[0].subject)
        self.assertIn(
            "Your blog was considered to be outside our Code of Code Publication",
            mail.outbox[0].body,
        )
        self.assertEqual(mail.outbox[0].to, [settings.EXPEL_LOG])
