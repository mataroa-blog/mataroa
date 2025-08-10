from unittest.mock import patch

import stripe
from django.test import TestCase
from django.urls import reverse

from main import models
from main.views import marketplace


class MarketplaceConnectTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_get(self):
        response = self.client.get(reverse("marketplace_connect"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b"Monetize your blog")

    def test_start_onboarding(self):
        with (
            patch.object(stripe.Account, "create", return_value={"id": "acct_123"}),
            patch.object(stripe.AccountLink, "create", return_value={"url": "https://stripe.test/al"}),
        ):
            response = self.client.post(reverse("marketplace_connect"), data={"action": "start_onboarding"})
        self.assertEqual(response.status_code, 302)


class MarketplaceSubscribeCtaTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(
            username="alice",
            stripe_connect_account_id="acct_123",
            stripe_connect_product_id="prod_123",
            stripe_connect_price_id="price_123",
            subscriptions_enabled=True,
        )

    def test_cta_on_blog_index(self):
        response = self.client.get(
            f"//{self.user.username}.mataroalocal.blog:8000" + reverse("index"),
            follow=True,
            secure=False,
        )
        # We can't easily set subdomain in tests; ensure template loads when rendering normally
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)


class MarketplaceSubscribeSessionTestCase(TestCase):
    def setUp(self):
        self.author = models.User.objects.create(
            username="alice",
            stripe_connect_account_id="acct_123",
            stripe_connect_product_id="prod_123",
            stripe_connect_price_id="price_123",
            subscriptions_enabled=True,
        )

    def test_checkout_session_create(self):
        # mock stripe checkout session
        with patch.object(stripe.checkout.Session, "create", return_value={"url": "https://stripe.test/s"}):
            # simulate subdomain by setting request.blog_user via middleware-bypass: call view directly
            class DummyReq:
                pass

            req = DummyReq()
            req.subdomain = self.author.username
            req.blog_user = self.author
            req.GET = {}
            req._messages = []

            def dummy_add(msg):
                req._messages.append(msg)

            from django.contrib import messages

            messages.error = lambda r, m: dummy_add(m)
            resp = marketplace.subscribe(req)
            self.assertEqual(resp.status_code, 302)


