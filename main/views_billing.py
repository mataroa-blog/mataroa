import logging
from datetime import datetime

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import mail_admins
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView

from main import forms

logger = logging.getLogger(__name__)


def _attach_card(user, card_token):
    """Create card on Stripe given a token, and attach it to user."""
    stripe.api_key = settings.STRIPE_API_KEY

    # create stripe customer for user if it does not exist
    if not user.stripe_customer_id:
        try:
            stripe_response = stripe.Customer.create()
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            return False
        user.stripe_customer_id = stripe_response.id
        user.save()

    # convert card token to payment method
    card = {
        "token": card_token,
    }
    try:
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card=card,
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        return False

    # attach payment method to customer
    try:
        stripe.PaymentMethod.attach(
            payment_method,
            customer=user.stripe_customer_id,
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        return False

    # if user has not already a card saved, aka not premium
    if not user.is_premium:
        # set new card as default payment method
        try:
            stripe.Customer.modify(
                user.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": payment_method["id"],
                },
            )
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            return False

    return True


def _get_subscription(stripe_customer_id, create=False):
    """Get subscription or create if it doesn't exist and second arg is True."""
    stripe.api_key = settings.STRIPE_API_KEY

    try:
        stripe_subs = stripe.Subscription.list(customer=stripe_customer_id)
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to get subscriptions from Stripe.")

    if len(stripe_subs.data) > 1:
        raise Exception("More than one subscription belonging to user.")

    if len(stripe_subs.data) == 1:
        subscription = stripe_subs.data[0]
        return subscription

    # if create arg is false, then return None to convey there is no subscription
    if not create:
        return None

    try:
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                }
            ],
            expand=["latest_invoice.payment_intent"],
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to create subscription on Stripe.")

    return subscription


def _get_payment_methods(stripe_customer_id):
    """Get user's payment methods and transform them into a dictionary."""
    stripe.api_key = settings.STRIPE_API_KEY

    # get default payment method id
    try:
        default_pm_id = stripe.Customer.retrieve(
            stripe_customer_id
        ).invoice_settings.default_payment_method
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to retrieve customer data from Stripe.")

    # get payment methods
    try:
        stripe_payment_methods = stripe.PaymentMethod.list(
            customer=stripe_customer_id,
            type="card",
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to retrieve payment methods from Stripe.")

    # normalise payment methods
    payment_methods = {}
    for stripe_pm in stripe_payment_methods.data:
        payment_methods[stripe_pm.id] = {
            "id": stripe_pm.id,
            "brand": stripe_pm.card.brand,
            "last4": stripe_pm.card.last4,
            "exp_month": stripe_pm.card.exp_month,
            "exp_year": stripe_pm.card.exp_year,
            "is_default": False,
        }
        if stripe_pm.id == default_pm_id:
            payment_methods[stripe_pm.id]["is_default"] = True

    return payment_methods


def _get_invoices(stripe_customer_id):
    """Get user's invoices and transform them into a dictionary."""
    stripe.api_key = settings.STRIPE_API_KEY

    # get user invoices
    try:
        stripe_invoices = stripe.Invoice.list(customer=stripe_customer_id)
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to retrieve invoices data from Stripe.")

    # normalise invoices objects
    invoice_list = []
    for stripe_inv in stripe_invoices.data:
        invoice_list.append(
            {
                "id": stripe_inv.id,
                "url": stripe_inv.hosted_invoice_url,
                "pdf": stripe_inv.invoice_pdf,
                "period_start": datetime.fromtimestamp(stripe_inv.period_start),
                "period_end": datetime.fromtimestamp(stripe_inv.period_end),
                "created": datetime.fromtimestamp(stripe_inv.created),
            }
        )

    return invoice_list


@login_required
def billing_index(request):
    """
    View method that shows the billing index, a summary of subscription and
    payment methods.
    """
    # respond for grandfathered users first
    if request.user.is_grandfathered:
        return render(
            request,
            "main/billing_index.html",
            {
                "is_grandfathered": True,
            },
        )

    # respond for monero case
    if request.user.monero_address:
        return render(request, "main/billing_index.html")

    stripe.api_key = settings.STRIPE_API_KEY

    # create stripe customer for user if it does not exist
    if not request.user.stripe_customer_id:
        try:
            stripe_response = stripe.Customer.create()
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            raise Exception("Failed to create customer on Stripe.")
        request.user.stripe_customer_id = stripe_response["id"]
        request.user.save()

    # get subscription if exists
    subscription = _get_subscription(request.user.stripe_customer_id)
    current_period_start = None
    current_period_end = None
    if subscription:
        current_period_start = datetime.utcfromtimestamp(
            subscription["current_period_start"]
        )
        current_period_end = datetime.utcfromtimestamp(
            subscription["current_period_end"]
        )

    # update user.is_premium in case of subscription being activated directly on Stripe
    if subscription and not request.user.is_premium:
        request.user.is_premium = True
        request.user.save()

    # update user.is_premium if subscription has been canceled directly on Stripe
    if subscription is None:
        request.user.is_premium = False
        request.user.save()

    # transform into list of values
    payment_methods = _get_payment_methods(request.user.stripe_customer_id).values()

    return render(
        request,
        "main/billing_index.html",
        {
            "stripe_customer_id": request.user.stripe_customer_id,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            "stripe_price_id": settings.STRIPE_PRICE_ID,
            "current_period_end": current_period_end,
            "current_period_start": current_period_start,
            "payment_methods": payment_methods,
            "invoice_list": _get_invoices(request.user.stripe_customer_id),
        },
    )


class BillingCard(LoginRequiredMixin, FormView):
    """View that receive a card token and starts subscription if not already existing."""

    form_class = forms.StripeForm
    template_name = "main/billing_card.html"
    success_url = reverse_lazy("billing_index")
    success_message = "new card added"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_customer_id"] = self.request.user.stripe_customer_id
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        context["stripe_price_id"] = settings.STRIPE_PRICE_ID
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            # create card on stripe
            card_created = _attach_card(
                request.user, form.cleaned_data.get("card_token")
            )
            if not card_created:
                form.add_error(None, "Failed to add card. Please try again.")
                return self.form_invalid(form)

            # create subscription on stripe
            subscription = _get_subscription(
                request.user.stripe_customer_id, create=True
            )

            # update user as premium subscribed
            if subscription and not request.user.is_premium:
                request.user.is_premium = True
                request.user.save()

            messages.success(request, self.success_message)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class BillingCardDelete(LoginRequiredMixin, View):
    """View that deletes a card from a user on Stripe."""

    template_name = "main/billing_card_confirm_delete.html"
    success_url = reverse_lazy("billing_index")
    success_message = "card deleted"
    slug_url_kwarg = "stripe_payment_method_id"

    # dict of valid payment methods with id as key and an obj as val
    stripe_payment_methods = {}

    def get_context_data(self, **kwargs):
        card_id = self.kwargs.get(self.slug_url_kwarg)
        context = {
            "card": self.stripe_payment_methods[card_id],
        }
        return context

    def post(self, request, *args, **kwargs):
        card_id = self.kwargs.get(self.slug_url_kwarg)
        try:
            stripe.PaymentMethod.detach(card_id)
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            messages.error(request, "payment processor unresponsive; please try again")
            return redirect(reverse_lazy("billing_index"))

        messages.success(request, self.success_message)
        return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.stripe_customer_id:
            mail_admins(
                "User tried to delete card without stripe_customer_id",
                f"user.id={request.user.id}\nuser.username={request.user.username}",
            )
            messages.error(
                request,
                "something has gone terribly wrong but we were just notified about it",
            )
            return redirect("dashboard")

        self.stripe_payment_methods = _get_payment_methods(
            request.user.stripe_customer_id
        )

        # check if card id is valid for user
        card_id = self.kwargs.get(self.slug_url_kwarg)
        if card_id not in self.stripe_payment_methods.keys():
            mail_admins(
                "User tried to delete card with invalid Stripe card ID",
                f"user.id={request.user.id}\nuser.username={request.user.username}",
            )
            messages.error(
                request,
                "this is not a valid card ID",
            )
            return redirect("dashboard")

        return super().dispatch(request, *args, **kwargs)


@login_required
def billing_card_default(request, stripe_payment_method_id):
    """View method that changes the default card of a user on Stripe."""
    if request.method == "POST":
        stripe_payment_methods = _get_payment_methods(request.user.stripe_customer_id)

        if stripe_payment_method_id not in stripe_payment_methods.keys():
            return HttpResponseBadRequest("Invalid Card ID.")

        stripe.api_key = settings.STRIPE_API_KEY
        try:
            stripe.Customer.modify(
                request.user.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": stripe_payment_method_id,
                },
            )
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            return HttpResponse("Could not change default card.", status=503)

        messages.success(request, "default card updated")
        return redirect("billing_index")


class BillingCancel(LoginRequiredMixin, View):
    """View that cancels a user subscription on Stripe."""

    template_name = "main/billing_subscription_cancel.html"
    success_url = reverse_lazy("billing_index")
    success_message = "premium subscription canceled"

    def post(self, request, *args, **kwargs):
        subscription = _get_subscription(request.user.stripe_customer_id)
        try:
            stripe.Subscription.delete(subscription["id"])
        except stripe.error.StripeError as ex:
            logger.error(str(ex))
            return HttpResponse("Subscription could not be canceled.", status=503)
        request.user.is_premium = False
        request.user.save()
        messages.success(request, self.success_message)
        return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def dispatch(self, request, *args, **kwargs):
        # redirect grandfathered users to dashboard
        if request.user.is_grandfathered:
            return redirect("dashboard")

        # if user has no customer id, redirect to billing_index to have it generated
        if not request.user.stripe_customer_id:
            return redirect("billing_index")

        # if user is not premium, redirect
        if not request.user.is_premium:
            return redirect("billing_index")

        subscription = _get_subscription(request.user.stripe_customer_id)
        if not subscription:
            return redirect("billing_index")

        return super().dispatch(request, *args, **kwargs)


@login_required
def billing_subscription(request):
    """
    View that creates a new subscription for user on Stripe,
    given they already have a card registered.
    """
    if request.method == "POST":
        # redirect grandfathered users to dashboard
        if request.user.is_grandfathered:
            return redirect("dashboard")

        subscription = _get_subscription(request.user.stripe_customer_id, create=True)
        if subscription:
            request.user.is_premium = True
            request.user.save()
        messages.success(request, "premium subscription enabled")
        return redirect("billing_index")
