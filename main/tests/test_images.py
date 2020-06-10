from django.test import TestCase
from django.urls import reverse

from main import models


class ImageCreateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_image_upload(self):
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
            self.assertTrue(models.Image.objects.filter(name="vulf").exists())
            self.assertEqual(models.Image.objects.get(name="vulf").extension, "jpeg")
            self.assertIsNotNone(models.Image.objects.get(name="vulf").slug)


class ImageCreateAnonTestCase(TestCase):
    def test_image_upload_anon(self):
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            response = self.client.post(reverse("image_list"), {"file": fp})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(reverse("login") in response.url)


class ImageDetailTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_detail(self):
        response = self.client.get(reverse("image_detail", args=(self.image.slug,)),)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("<h1>vulf</h1>", response.content.decode("utf-8"))
        self.assertContains(response, "Uploaded on")


class ImageUpdateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_update(self):
        new_data = {
            "name": "new vulf",
        }
        self.client.post(reverse("image_update", args=(self.image.slug,)), new_data)
        updated_image = models.Image.objects.get(id=self.image.id)
        self.assertEqual(updated_image.name, new_data["name"])


class ImageUpdateAnonTestCase(TestCase):
    """Tests non logged in user cannot update image."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

    def test_image_update(self):
        new_data = {
            "name": "new vulf",
        }
        self.client.post(reverse("image_update", args=(self.image.slug,)), new_data)
        image_now = models.Image.objects.get(id=self.image.id)
        self.assertEqual(image_now.name, "vulf")


class ImageUpdateNotOwnTestCase(TestCase):
    """Tests user cannot update other user's image name."""

    def setUp(self):
        self.victim = models.User.objects.create(username="bob")
        self.victim.set_password("abcdef123456")
        self.victim.save()
        self.client.login(username="bob", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

        self.attacker = models.User.objects.create(username="alice")
        self.attacker.set_password("abcdef123456")
        self.attacker.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_image_update_not_own(self):
        new_data = {
            "name": "bad vulf",
        }
        self.client.post(reverse("image_update", args=(self.image.slug,)), new_data)
        image_now = models.Image.objects.get(id=self.image.id)
        self.assertEqual(image_now.name, "vulf")


class ImageDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_delete(self):
        self.client.post(reverse("image_delete", args=(self.image.slug,)))
        self.assertFalse(
            models.Image.objects.filter(name="vulf", owner=self.user).exists()
        )


class ImageDeleteAnonTestCase(TestCase):
    """Tests non logged in user cannot delete image."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

    def test_image_delete_anon(self):
        self.client.post(reverse("image_delete", args=(self.image.slug,)))
        self.assertTrue(
            models.Image.objects.filter(name="vulf", owner=self.user).exists()
        )


class ImageDeleteNotOwnTestCase(TestCase):
    """Tests user cannot delete other's image."""

    def setUp(self):
        self.victim = models.User.objects.create(username="bob")
        self.victim.set_password("abcdef123456")
        self.victim.save()
        self.client.login(username="bob", password="abcdef123456")
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

        self.attacker = models.User.objects.create(username="alice")
        self.attacker.set_password("abcdef123456")
        self.attacker.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_image_delete_not_own(self):
        self.client.post(reverse("image_delete", args=(self.image.slug,)))
        self.assertTrue(
            models.Image.objects.filter(name="vulf", owner=self.victim).exists()
        )
