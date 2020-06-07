from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from main import models


class PostCreateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_post_create(self):
        data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        response = self.client.post(reverse("post_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.Post.objects.get(title=data["title"]))


class PostCreateAnonTestCase(TestCase):
    """Tests non logged in user cannot create post."""

    def test_post_create_anon(self):
        data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        response = self.client.post(reverse("post_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse("login") in response.url)


class PostCreateDraftTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
            "published_at": "",
        }
        self.client.post(reverse("post_create"), self.data)

    def test_post_create_draft(self):
        """Test draft post gets created."""
        self.assertTrue(models.Post.objects.get(title=self.data["title"]))

    def test_post_draft_index(self):
        """Test draft post appears on blog index as draft."""
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DRAFT")


class PostCreateDraftAnonTestCase(TestCase):
    """Test draft post does not appear on blog index for non-logged in users."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data_published = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        models.Post.objects.create(owner=self.user, **self.data_published)
        self.data_nonpublished = {
            "title": "Draft post",
            "slug": "draft-post",
            "body": "Incomplete content sentence.",
            "published_at": None,
        }
        models.Post.objects.create(owner=self.user, **self.data_nonpublished)

    def test_post_draft_index(self):
        response = self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.data_published["title"])
        self.assertNotContains(response, self.data_nonpublished["title"])


class PostDetailTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_detail(self):
        response = self.client.get(
            reverse("post_detail", args=(self.post.slug,)),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.data["title"])
        self.assertContains(response, self.data["body"])


class PostUpdateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_update(self):
        new_data = {
            "title": "Updated post",
            "slug": "updated-new-post",
            "body": "Updated content sentence.",
        }
        self.client.post(reverse("post_update", args=(self.post.slug,)), new_data)
        updated_post = models.Post.objects.get(id=self.post.id)
        self.assertTrue(updated_post.title, new_data["title"])
        self.assertTrue(updated_post.slug, new_data["slug"])
        self.assertTrue(updated_post.body, new_data["body"])


class PostUpdateNotOwnTestCase(TestCase):
    """Tests user cannot update other user's post."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_update_not_own(self):
        new_data = {
            "title": "Updated post",
            "slug": "updated-new-post",
            "body": "Updated content sentence.",
        }
        self.client.post(reverse("post_update", args=(self.post.slug,)), new_data)
        updated_post = models.Post.objects.get(id=self.post.id)
        self.assertTrue(updated_post.title, new_data["title"])
        self.assertTrue(updated_post.slug, new_data["slug"])
        self.assertTrue(updated_post.body, new_data["body"])


class PostUpdateAnonTestCase(TestCase):
    """Tests non logged in user cannot update post."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_update_anon(self):
        new_data = {
            "title": "Updated post",
            "slug": "updated-new-post",
            "body": "Updated content sentence.",
        }
        self.client.post(reverse("post_update", args=(self.post.slug,)), new_data)
        post_now = models.Post.objects.get(id=self.post.id)
        self.assertTrue(post_now.title, new_data["title"])
        self.assertTrue(post_now.slug, new_data["slug"])
        self.assertTrue(post_now.body, new_data["body"])

    def test_post_update_anon_subdomain(self):
        new_data = {
            "title": "Updated post",
            "slug": "updated-new-post",
            "body": "Updated content sentence.",
        }
        self.client.post(
            reverse("post_update", args=(self.post.slug,)),
            new_data,
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        post_now = models.Post.objects.get(id=self.post.id)
        self.assertTrue(post_now.title, new_data["title"])
        self.assertTrue(post_now.slug, new_data["slug"])
        self.assertTrue(post_now.body, new_data["body"])


class PostDeleteTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_delete(self):
        self.client.post(
            reverse("post_delete", args=(self.post.slug,)),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertFalse(
            models.Post.objects.filter(slug=self.data["slug"], owner=self.user).exists()
        )


class PostDeleteNoSubdomainTestCase(TestCase):
    """Tests user cannot delete post without being in their subdomain."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.user.set_password("abcdef123456")
        self.user.save()
        self.client.login(username="alice", password="abcdef123456")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_delete_no_subdomain(self):
        self.client.post(reverse("post_delete", args=(self.post.slug,)))
        self.assertTrue(
            models.Post.objects.filter(slug=self.data["slug"], owner=self.user).exists()
        )


class PostDeleteAnonTestCase(TestCase):
    """Tests non logged in user cannot delete post."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_delete_anon(self):
        self.client.post(reverse("post_delete", args=(self.post.slug,)))
        self.assertTrue(
            models.Post.objects.filter(slug=self.data["slug"], owner=self.user).exists()
        )


class PostDeleteNotOwnTestCase(TestCase):
    """Tests user cannot delete other's post."""

    def setUp(self):
        self.victim = models.User.objects.create(username="bob")
        self.data = {
            "title": "New post",
            "slug": "new-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.victim, **self.data)

        self.attacker = models.User.objects.create(username="alice")
        self.attacker.set_password("abcdef123456")
        self.attacker.save()
        self.client.login(username="alice", password="abcdef123456")

    def test_post_delete_not_own(self):
        self.client.post(
            reverse("post_delete", args=(self.post.slug,)),
            HTTP_HOST=self.victim.username + "." + settings.CANONICAL_HOST,
        )
        self.assertTrue(
            models.Post.objects.filter(
                slug=self.data["slug"], owner=self.victim
            ).exists()
        )

    def test_post_delete_not_own_no_subdomain(self):
        self.client.post(reverse("post_delete", args=(self.post.slug,)))
        self.assertTrue(
            models.Post.objects.filter(
                slug=self.data["slug"], owner=self.victim
            ).exists()
        )
