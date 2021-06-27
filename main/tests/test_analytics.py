from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from main import models


class PostAnalyticAnonTestCase(TestCase):
    """Test post analytics for non logged in users."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)
        self.client.logout()

    def test_post_analytic_anon(self):
        response = self.client.get(
            reverse("post_detail", args=(self.post.slug,)),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.AnalyticPost.objects.filter(post=self.post).count(), 1)


class PostAnalyticTestCase(TestCase):
    """Test post analytics for logged in users do not count."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_post_analytic_logged_in(self):
        response = self.client.get(
            reverse("post_detail", args=(self.post.slug,)),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.AnalyticPost.objects.filter(post=self.post).exists())


class PageAnalyticAnonTestCase(TestCase):
    """Test page analytics for non logged in users."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "About",
            "slug": "about",
            "body": "About this blog.",
            "is_hidden": False,
        }
        self.page = models.Page.objects.create(owner=self.user, **self.data)
        self.client.logout()

    def test_page_analytic_anon(self):
        response = self.client.get(
            reverse("page_detail", args=(self.page.slug,)),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            models.AnalyticPage.objects.filter(path=self.page.slug).count(), 1
        )


class PageAnalyticTestCase(TestCase):
    """Test generic page analytics for logged in users do not count."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "About",
            "slug": "about",
            "body": "About this blog.",
            "is_hidden": False,
        }
        self.page = models.Page.objects.create(owner=self.user, **self.data)

    def test_page_analytic_logged_in(self):
        response = self.client.get(
            reverse("page_detail", args=(self.page.slug,)),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            models.AnalyticPage.objects.filter(path=self.page.slug).exists()
        )


class PageAnalyticIndexTestCase(TestCase):
    """Test 'index' special page analytics."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")

    def test_index_analytic(self):
        response = self.client.get(
            reverse("index"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.AnalyticPage.objects.filter(path="index").count(), 1)


class PageAnalyticRSSTestCase(TestCase):
    """Test 'rss' special page analytics."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")

    def test_rss_analytic(self):
        response = self.client.get(
            reverse("rss_feed"),
            # needs HTTP_HOST because we need to request it on the subdomain
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.AnalyticPage.objects.filter(path="rss").count(), 1)


class AnalyticListTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

    def test_analytic_list(self):
        response = self.client.get(
            reverse("analytic_list"),
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "List of pages:")
        self.assertContains(response, "index")
        self.assertContains(response, "rss")

        self.assertContains(response, "List of posts:")
        self.assertContains(response, "Welcome post")


class PostAnalyticDetailTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "Welcome post",
            "slug": "welcome-post",
            "body": "Content sentence.",
        }
        self.post = models.Post.objects.create(owner=self.user, **self.data)

        # register one sample post analytic
        self.client.logout()  # need to logout for analytic to be counted
        self.client.get(
            reverse("post_detail", args=(self.post.slug,)),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )

        # need to login again to access analytic post detail dashboard page
        self.client.force_login(self.user)

    def test_post_analytic_detail(self):
        response = self.client.get(
            reverse("analytic_post_detail", args=(self.post.slug,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="analytics-chart">')
        self.assertContains(
            response,
            '<svg version="1.1" viewBox="0 0 500 192" xmlns="http://www.w3.org/2000/svg">',
        )
        self.assertContains(response, "1 hits")


class PageAnalyticDetailTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.data = {
            "title": "About",
            "slug": "about",
            "body": "About this blog.",
            "is_hidden": False,
        }
        self.page = models.Page.objects.create(owner=self.user, **self.data)

        # register one sample page analytic
        self.client.logout()  # need to logout for analytic to be counted

        # register one sample page analytic
        self.client.get(
            reverse("page_detail", args=(self.page.slug,)),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )

        # need to login again to access analytic page detail dashboard page
        self.client.force_login(self.user)

    def test_page_analytic_detail(self):
        response = self.client.get(
            reverse("analytic_page_detail", args=(self.page.slug,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="analytics-chart">')
        self.assertContains(
            response,
            '<svg version="1.1" viewBox="0 0 500 192" xmlns="http://www.w3.org/2000/svg">',
        )
        self.assertContains(response, "1 hits")


class PageAnalyticDetailIndexTestCase(TestCase):
    """Test analytic detail for 'index' special page."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

        # logout so that analytic is counted
        self.client.logout()

        # register one sample index page analytic
        self.client.get(
            reverse("index"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )

        # login again to access analytic page detail dashboard page
        self.client.force_login(self.user)

    def test_page_analytic_detail(self):
        response = self.client.get(
            reverse("analytic_page_detail", args=("index",)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="analytics-chart">')
        self.assertContains(
            response,
            '<svg version="1.1" viewBox="0 0 500 192" xmlns="http://www.w3.org/2000/svg">',
        )
        self.assertContains(response, "1 hits")


class PageAnalyticDetailRSSTestCase(TestCase):
    """Test analytic detail for 'rss' special page."""

    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

        # logout so that analytic is counted
        self.client.logout()

        # register one sample rss page analytic
        self.client.get(
            reverse("rss_feed"),
            HTTP_HOST=self.user.username + "." + settings.CANONICAL_HOST,
        )

        # login again to access analytic page detail dashboard page
        self.client.force_login(self.user)

    def test_page_analytic_detail(self):
        response = self.client.get(
            reverse("analytic_page_detail", args=("rss",)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="analytics-chart">')
        self.assertContains(
            response,
            '<svg version="1.1" viewBox="0 0 500 192" xmlns="http://www.w3.org/2000/svg">',
        )
        self.assertContains(response, "1 hits")
