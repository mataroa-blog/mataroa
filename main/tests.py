from django.test import TestCase
from django.urls import reverse

from main import models


class IndexTestCase(TestCase):
    def test_index(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)


class UserCreateTestCase(TestCase):
    def test_user_creation(self):
        data = {
            "username": "john",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
        }
        response = self.client.post(reverse("user_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.User.objects.get(username=data["username"]))


class LoginTestCase(TestCase):
    def setUp(self):
        user = models.User.objects.create(username="john")
        user.set_password("abcdef123456")
        user.save()

    def test_login(self):
        data = {
            "username": "john",
            "password": "abcdef123456",
        }
        response_login = self.client.post(reverse("login"), data)
        self.assertEqual(response_login.status_code, 302)

        response_index = self.client.get(reverse("index"))
        user = response_index.context.get("user")
        self.assertTrue(user.is_authenticated)

    def test_login_invalid(self):
        data = {
            "username": "john",
            "password": "wrong_password",
        }
        response_login = self.client.post(reverse("login"), data)
        self.assertEqual(response_login.status_code, 200)

        response_index = self.client.get(reverse("index"))
        self.assertEqual(response_index.status_code, 200)

        user = response_index.context.get("user")
        self.assertFalse(user.is_authenticated)


class LogoutTestCase(TestCase):
    def setUp(self):
        user = models.User.objects.create(username="john")
        user.set_password("abcdef123456")
        user.save()
        data = {
            "username": "john",
            "password": "abcdef123456",
        }
        self.client.post(reverse("login"), data)

    def test_logout(self):
        response_logout = self.client.get(reverse("logout"))
        self.assertEqual(response_logout.status_code, 200)

        response_index = self.client.get(reverse("index"))
        user = response_index.context.get("user")
        self.assertFalse(user.is_authenticated)


class UserDetailTestCase(TestCase):
    def setUp(self):
        user = models.User.objects.create(username="john")
        user.set_password("abcdef123456")
        user.save()
        data = {
            "username": "john",
            "password": "abcdef123456",
        }
        self.client.post(reverse("login"), data)
        self.user = models.User.objects.get(username=data["username"])

    def test_profile(self):
        response = self.client.get(reverse("user_detail", args=(self.user.id,)))
        self.assertEqual(response.status_code, 200)


class UserUpdateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="john")
        self.user.set_password("abcdef123456")
        self.user.save()

    def test_user_update(self):
        data = {"username": "john2", "email": "john2@example.com"}
        response = self.client.post(reverse("user_update", args=(self.user.id,)), data)
        self.assertEqual(response.status_code, 302)
        updated_user = models.User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, data["username"])
        self.assertEqual(updated_user.email, data["email"])


class UserPasswordChangeTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="john")
        self.user.set_password("abcdef123456")
        self.user.save()

    def test_user_password_change(self):
        data = {"username": "john2", "email": "john2@example.com"}
        response = self.client.post(reverse("user_update", args=(self.user.id,)), data)
        self.assertEqual(response.status_code, 302)
        updated_user = models.User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, data["username"])
        self.assertEqual(updated_user.email, data["email"])


class UserDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="john")
        self.user.set_password("abcdef123456")
        self.user.save()

    def test_user_delete(self):
        response = self.client.post(reverse("user_delete", args=(self.user.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(models.User.objects.filter(id=self.user.id).exists())
