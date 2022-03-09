from django.test import TestCase
from django.urls import reverse

from main import models


class AdminDashboardAnonTestCase(TestCase):
    def test_admin_dashboard_get(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_admin_dashboard_post(self):
        response = self.client.post(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 404)


class AdminDashboardNonadminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_admin_dashboard_nonadmin(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 404)


class AdminDashboardAdminTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice", is_superuser=True)
        self.client.force_login(self.user)

    def test_admin_dashboard_admin(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
