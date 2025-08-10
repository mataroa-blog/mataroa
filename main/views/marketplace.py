import logging
import json
from typing import Optional

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from main import models, util


logger = logging.getLogger(__name__)


def _ensure_connect_account(user: models.User) -> str:
    """Create a Stripe Connect Express account for the author if missing."""
    if user.stripe_connect_account_id:
        return user.stripe_connect_account_id

    stripe.api_key = settings.STRIPE_API_KEY
    try:
        account = stripe.Account.create(
            type="express",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_type="individual",
            business_profile={
                "name": user.blog_title or user.username,
                "product_description": "Blog subscriptions",
                "url": util.get_protocol() + "//" + settings.CANONICAL_HOST,
            },
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to create Stripe Connect account.") from ex

    user.stripe_connect_account_id = account["id"]
    user.save(update_fields=["stripe_connect_account_id"])
    return user.stripe_connect_account_id


def _create_account_link(account_id: str, return_to: str, refresh_to: str) -> str:
    stripe.api_key = settings.STRIPE_API_KEY
    try:
        al = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_to,
            return_url=return_to,
            type="account_onboarding",
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to create Stripe Account Link.") from ex
    return al["url"]


def _create_login_link(account_id: str) -> Optional[str]:
    stripe.api_key = settings.STRIPE_API_KEY
    try:
        ll = stripe.Account.create_login_link(account_id)
        return ll["url"]
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        return None


def _ensure_product_price(user: models.User) -> None:
    """Ensure a platform Product and Price exist for the author's subscription.

    Subscriptions are created on the platform with transfer_data to the author's
    connected account. Product/Price therefore live on the platform.
    """
    stripe.api_key = settings.STRIPE_API_KEY

    # Create or update Product
    if not user.stripe_connect_product_id:
        try:
            product = stripe.Product.create(
                name=f"{user.blog_title or user.username} – Blog Subscription",
                metadata={
                    "author_user_id": str(user.id),
                    "author_username": user.username,
                },
            )
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            raise Exception("Failed to create Product on Stripe.") from ex
        user.stripe_connect_product_id = product["id"]

    # Always create a new Price when amount changes; Prices are immutable
    if not user.stripe_connect_price_id:
        must_create_price = True
    else:
        # We cannot read amount of an existing price without an API call
        # Create new price if local amount doesn't match remote, else reuse
        must_create_price = True

    if must_create_price:
        try:
            price = stripe.Price.create(
                unit_amount=user.subscription_price_cents,
                currency="usd",
                recurring={"interval": "month"},
                product=user.stripe_connect_product_id,
                metadata={
                    "author_user_id": str(user.id),
                    "author_username": user.username,
                },
            )
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            raise Exception("Failed to create Price on Stripe.") from ex
        user.stripe_connect_price_id = price["id"]

    user.save(
        update_fields=[
            "stripe_connect_product_id",
            "stripe_connect_price_id",
        ]
    )


class MarketplaceConnect(LoginRequiredMixin, View):
    template_name = "main/marketplace_connect.html"

    def get(self, request):
        charges_enabled = None
        payouts_enabled = None
        if request.user.stripe_connect_account_id and settings.STRIPE_API_KEY:
            try:
                stripe.api_key = settings.STRIPE_API_KEY
                acct = stripe.Account.retrieve(request.user.stripe_connect_account_id)
                charges_enabled = acct.get("charges_enabled")
                payouts_enabled = acct.get("payouts_enabled")
            except stripe.error.StripeError as ex:
                logger.info("could not retrieve connect account: %s", ex)

        return render(
            request,
            self.template_name,
            {
                "has_account": bool(request.user.stripe_connect_account_id),
                "account_id": request.user.stripe_connect_account_id,
                "subscriptions_enabled": request.user.subscriptions_enabled,
                "price_cents": request.user.subscription_price_cents,
                "price_dollars": request.user.subscription_price_cents / 100,
                "price_id": request.user.stripe_connect_price_id,
                "charges_enabled": charges_enabled,
                "payouts_enabled": payouts_enabled,
            },
        )

    def post(self, request):
        action = request.POST.get("action")
        try:
            if action == "start_onboarding":
                account_id = _ensure_connect_account(request.user)
                return_url = (
                    f"{util.get_protocol()}//{settings.CANONICAL_HOST}"
                    + reverse("marketplace_connect")
                )
                refresh_url = return_url
                return redirect(_create_account_link(account_id, return_url, refresh_url))

            elif action == "open_dashboard":
                if not request.user.stripe_connect_account_id:
                    messages.error(request, "Stripe account not found.")
                    return redirect("marketplace_connect")
                login_url = _create_login_link(request.user.stripe_connect_account_id)
                if login_url:
                    return redirect(login_url)
                messages.error(request, "Could not create Stripe login link.")
                return redirect("marketplace_connect")

            elif action == "enable_subscriptions":
                if not request.user.stripe_connect_account_id:
                    messages.error(request, "Complete Stripe onboarding first.")
                    return redirect("marketplace_connect")

                # Allow updating price via form
                price_cents_str = request.POST.get("price_cents")
                if price_cents_str:
                    try:
                        request.user.subscription_price_cents = int(price_cents_str)
                    except ValueError:
                        return HttpResponseBadRequest("Invalid price.")

                _ensure_product_price(request.user)
                request.user.subscriptions_enabled = True
                request.user.save(
                    update_fields=[
                        "subscription_price_cents",
                        "subscriptions_enabled",
                    ]
                )
                messages.success(request, "Paid subscriptions enabled.")
                return redirect("marketplace_connect")

            elif action == "disable_subscriptions":
                request.user.subscriptions_enabled = False
                request.user.save(update_fields=["subscriptions_enabled"])
                messages.success(request, "Paid subscriptions disabled.")
                return redirect("marketplace_connect")

        except Exception as ex:  # noqa: BLE001
            logger.error(str(ex))
            messages.error(request, "Operation failed. Please try again.")
            return redirect("marketplace_connect")

        return HttpResponseBadRequest("Unknown action.")


def subscribe(request):
    """Create a Checkout Session for a reader to subscribe to this blog."""
    if not hasattr(request, "subdomain"):
        messages.error(request, "Subscriptions are only available in blog context.")
        return redirect("index")

    author = request.blog_user
    if not author.subscriptions_enabled:
        messages.error(request, "Subscriptions are not enabled for this blog.")
        return redirect("index")
    if not author.stripe_connect_account_id or not author.stripe_connect_price_id:
        messages.error(request, "Subscriptions setup incomplete for this blog.")
        return redirect("index")

    stripe.api_key = settings.STRIPE_API_KEY
    success_url = f"{author.blog_absolute_url}{reverse('index')}?subscribed=1"
    cancel_url = (
        f"{util.get_protocol()}//{author.username}.{settings.CANONICAL_HOST}"
        + reverse("index")
    )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": author.stripe_connect_price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            automatic_tax={"enabled": False},
            allow_promotion_codes=False,
            subscription_data={
                "transfer_data": {
                    "destination": author.stripe_connect_account_id,
                },
                "metadata": {
                    "author_user_id": str(author.id),
                    "author_username": author.username,
                },
            },
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        messages.error(request, "Payment processor error. Please try again later.")
        return redirect("index")

    return redirect(session["url"])  # type: ignore[no-any-return]


class SubscribersList(LoginRequiredMixin, View):
    template_name = "main/marketplace_subscribers.html"

    def get(self, request):
        subs = models.ReaderSubscription.objects.filter(owner=request.user)
        return render(request, self.template_name, {"subscriptions": subs})


@csrf_exempt
def marketplace_stripe_webhook(request):
    """Handle webhooks for marketplace subscriptions (platform + connected)."""

    stripe.api_key = settings.STRIPE_API_KEY
    try:
        data = stripe.Event.construct_from(
            json.loads(request.body), stripe.api_key
        )
    except Exception as ex:  # noqa: BLE001
        logger.error(str(ex))
        return HttpResponse(status=400)

    try:
        if data.type == "checkout.session.completed":
            session = data.data.object
            if getattr(session, "mode", "") != "subscription":
                return HttpResponse()

            subscription_id = session.get("subscription")
            customer_id = session.get("customer")
            email = None
            if session.get("customer_details"):
                email = session["customer_details"].get("email")

            # Retrieve subscription to access metadata
            sub = stripe.Subscription.retrieve(subscription_id)
            author_user_id = sub["metadata"].get("author_user_id")
            if not author_user_id:
                return HttpResponse()
            author = models.User.objects.filter(id=int(author_user_id)).first()
            if not author:
                return HttpResponse()

            models.ReaderSubscription.objects.update_or_create(
                owner=author,
                stripe_subscription_id=subscription_id,
                defaults={
                    "stripe_account_id": author.stripe_connect_account_id or "",
                    "stripe_customer_id": customer_id,
                    "email": email,
                    "status": "active",
                },
            )

        elif data.type in ("customer.subscription.deleted", "customer.subscription.updated"):
            subscription = data.data.object
            status = subscription.get("status")
            rs = models.ReaderSubscription.objects.filter(
                stripe_subscription_id=subscription.get("id")
            ).first()
            if rs:
                rs.status = status or rs.status
                rs.save(update_fields=["status"])

    except Exception as ex:  # noqa: BLE001
        logger.error(str(ex))
        return HttpResponse(status=400)

    return HttpResponse()


