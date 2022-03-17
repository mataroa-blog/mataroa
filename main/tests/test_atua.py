from django.test import TestCase
from django.urls import reverse

from main import models


class AtuaAnonTestCase(TestCase):
    def test_atua_users_get(self):
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 404)

    def test_atua_users_post(self):
        response = self.client.post(reverse("admin_users"))
        self.assertEqual(response.status_code, 404)

    def test_atua_posts_get(self):
        response = self.client.get(reverse("admin_posts"))
        self.assertEqual(response.status_code, 404)

    def test_atua_posts_post(self):
        response = self.client.post(reverse("admin_posts"))
        self.assertEqual(response.status_code, 404)

    def test_atua_pages_get(self):
        response = self.client.get(reverse("admin_pages"))
        self.assertEqual(response.status_code, 404)

    def test_atua_pages_post(self):
        response = self.client.post(reverse("admin_pages"))
        self.assertEqual(response.status_code, 404)


class AtuaNonadminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_atua_users_nonadmin(self):
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 404)

    def test_atua_posts_nonadmin(self):
        response = self.client.get(reverse("admin_posts"))
        self.assertEqual(response.status_code, 404)

    def test_atua_pages_nonadmin(self):
        response = self.client.get(reverse("admin_pages"))
        self.assertEqual(response.status_code, 404)


class AtuaAdminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice", is_superuser=True)
        self.client.force_login(self.user)

    def test_atua_users_admin(self):
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 200)

    def test_atua_posts_admin(self):
        response = self.client.get(reverse("admin_posts"))
        self.assertEqual(response.status_code, 200)

    def test_atua_pages_admin(self):
        response = self.client.get(reverse("admin_pages"))
        self.assertEqual(response.status_code, 200)
