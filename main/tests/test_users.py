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
            "username": "alice",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
            "blog_title": "New blog",
        }
        response = self.client.post(reverse("user_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.User.objects.get(username=data["username"]))


class UserCreateDisallowedTestCase(TestCase):
    def test_user_creation(self):
        data = {
            "username": "settings",
            "password1": "abcdef123456",
            "password2": "abcdef123456",
            "blog_title": "New blog",
        }
        response = self.client.post(reverse("user_create"), data)
        self.assertContains(response, b"This username is not available.")


class LoginTestCase(TestCase):
    def setUp(self):
        user = models.User.objects.create(username="alice")
        user.set_password("abcdef123456")
        user.save()

    def test_login(self):
        data = {
            "username": "alice",
            "password": "abcdef123456",
        }
        response_login = self.client.post(reverse("login"), data)
        self.assertEqual(response_login.status_code, 302)

        response_index = self.client.get(reverse("dashboard"))
        user = response_index.context.get("user")
        self.assertTrue(user.is_authenticated)

    def test_login_invalid(self):
        data = {
            "username": "alice",
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
        user = models.User.objects.create(username="alice")
        user.set_password("abcdef123456")
        user.save()
        data = {
            "username": "alice",
            "password": "abcdef123456",
        }
        self.client.post(reverse("login"), data)

    def test_logout(self):
        response_logout = self.client.get(reverse("logout"))
        self.assertEqual(response_logout.status_code, 302)

        response_index = self.client.get(reverse("index"))
        user = response_index.context.get("user")
        self.assertFalse(user.is_authenticated)


class UserDetailTestCase(TestCase):
    def setUp(self):
        user = models.User.objects.create(username="alice")
        user.set_password("abcdef123456")
        user.save()
        data = {
            "username": "alice",
            "password": "abcdef123456",
        }
        self.client.post(reverse("login"), data)
        self.user = models.User.objects.get(username=data["username"])

    def test_user_detail(self):
        response = self.client.get(reverse("user_detail", args=(self.user.id,)))
        self.assertEqual(response.status_code, 200)


class UserDetailNotOwnTestCase(TestCase):
    """Tests user cannot access another user's detail page."""

    def setUp(self):
        attacker_data = {
            "username": "alice",
            "password": "abcdef123456",
        }
        attacker = models.User.objects.create(username=attacker_data["username"])
        attacker.set_password(attacker_data["password"])
        attacker.save()
        self.client.post(reverse("login"), attacker_data)
        self.attacker = models.User.objects.get(username=attacker_data["username"])

        self.victim = models.User.objects.create(username="bob")

    def test_user_detail_not_own(self):
        response = self.client.get(reverse("user_detail", args=(self.victim.id,)))
        self.assertEqual(response.status_code, 403)


class UserUpdateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_user_update(self):
        data = {
            "username": "alice-updated",
            "email": "alice_updated@example.com",
            "blog_title": "Updated title",
        }
        response = self.client.post(reverse("user_update", args=(self.user.id,)), data)
        self.assertEqual(response.status_code, 302)
        updated_user = models.User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, data["username"])
        self.assertEqual(updated_user.email, data["email"])


class UserUpdateNotOwnTestCase(TestCase):
    """Tests user cannot update another user's details."""

    def setUp(self):
        attacker_data = {
            "username": "alice",
            "password": "abcdef123456",
        }
        attacker = models.User.objects.create(username=attacker_data["username"])
        attacker.set_password(attacker_data["password"])
        attacker.save()
        self.client.post(reverse("login"), attacker_data)
        self.attacker = models.User.objects.get(username=attacker_data["username"])

        victim_data = {
            "username": "bob",
            "email": "bob@example.com",
            "blog_title": "Bob blog",
        }
        self.victim = models.User.objects.create(**victim_data)

    def test_user_update_not_own(self):
        data = {
            "username": "bob_sucks",
            "email": "bob_sucks@example.com",
            "blog_title": "Bob blog sucks",
        }
        response = self.client.post(
            reverse("user_update", args=(self.victim.id,)), data
        )
        self.assertEqual(response.status_code, 403)
        victim_now = models.User.objects.get(id=self.victim.id)
        self.assertEqual(victim_now.username, self.victim.username)
        self.assertEqual(victim_now.email, self.victim.email)
        self.assertEqual(victim_now.blog_title, self.victim.blog_title)


class UserPasswordChangeTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_user_password_change(self):
        data = {
            "old_password": "abcdef123456",
            "new_password1": "987wyxtuv",
            "new_password2": "987wyxtuv",
        }
        response = self.client.post(reverse("password_change"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.login(username="alice", password="987wyxtuv"))


class UserDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_user_delete(self):
        response = self.client.post(reverse("user_delete", args=(self.user.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(models.User.objects.filter(id=self.user.id).exists())


class UserDeleteNotOwnTestCase(TestCase):
    """Tests user cannot delete other user."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

        self.victim = models.User.objects.create(username="bob")

    def test_user_delete(self):
        response = self.client.post(reverse("user_delete", args=(self.victim.id,)))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(models.User.objects.filter(id=self.victim.id).exists())


class UserUpdateCommentsOnTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_user_comments_on(self):
        data = {
            "username": "alice",
            "comments_on": True,
        }
        response = self.client.post(reverse("user_update", args=(self.user.id,)), data)
        self.assertEqual(response.status_code, 302)
        updated_user = models.User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.comments_on, data["comments_on"])
