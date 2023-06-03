from django.test import TestCase
from django.urls import reverse

from main import models


class ImageCreateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

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
        self.client.force_login(self.user)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_detail(self):
        response = self.client.get(
            reverse("image_detail", args=(self.image.slug,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertInHTML("<h1>vulf</h1>", response.content.decode("utf-8"))
        self.assertContains(response, "Uploaded on")


class ImageDetailNotOwnTestCase(TestCase):
    """Tests user cannot open image detail page of another user's image."""

    def setUp(self):
        self.victim = models.User.objects.create(username="bob")
        self.client.force_login(self.victim)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

        self.attacker = models.User.objects.create(username="alice")
        self.client.force_login(self.attacker)

    def test_image_detail_not_own(self):
        response = self.client.get(reverse("image_detail", args=(self.image.slug,)))
        self.assertEqual(response.status_code, 403)


class ImageDetailUsedByTestCase(TestCase):
    """Tests used by posts feature works."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": f'This is Vulfpeck\n<img src="/images/{self.image.filename}">',
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_image_detail(self):
        response = self.client.get(
            reverse("image_detail", args=(self.image.slug,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Used by posts:")
        self.assertContains(response, "New post")


class ImageRawTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_raw(self):
        response = self.client.get(
            reverse("image_raw", args=(self.image.slug, self.image.extension)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.image.data.tobytes(), response.content)


class ImageRawWrongExtTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")

    def test_image_raw(self):
        response = self.client.get(
            reverse("image_raw", args=(self.image.slug, "png")),
        )
        self.assertEqual(response.status_code, 404)


class ImageRawNotFoundTestCase(TestCase):
    def setUp(self):
        self.slug = "nonexistent-slug"
        self.extension = "jpeg"

    def test_image_raw(self):
        response = self.client.get(
            reverse("image_raw", args=(self.slug, self.extension)),
        )
        self.assertEqual(response.status_code, 404)


class ImageUpdateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
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
        self.client.force_login(self.user)
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
        self.client.force_login(self.victim)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

        self.attacker = models.User.objects.create(username="alice")
        self.client.force_login(self.attacker)

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
        self.client.force_login(self.user)
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
        self.client.force_login(self.user)
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
        self.client.force_login(self.victim)
        with open("main/tests/testdata/vulf.jpeg", "rb") as fp:
            self.client.post(reverse("image_list"), {"file": fp})
        self.image = models.Image.objects.get(name="vulf")
        self.client.logout()

        self.attacker = models.User.objects.create(username="alice")
        self.client.force_login(self.attacker)

    def test_image_delete_not_own(self):
        self.client.post(reverse("image_delete", args=(self.image.slug,)))
        self.assertTrue(
            models.Image.objects.filter(name="vulf", owner=self.victim).exists()
        )
