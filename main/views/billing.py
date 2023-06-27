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

from main import forms, util

logger = logging.getLogger(__name__)


# def _get_client_secret(stripe_customer_id):
#     try:
#         stripe_invoice = stripe.Invoice.upcoming(customer=stripe_customer_id)
#     except stripe.error.StripeError as ex:
#         logger.error(str(ex))
#         raise Exception("Failed to get latest invoice from Stripe.")

#     try:
#         stripe_payment_intent = stripe.PaymentIntent.retrieve(stripe_invoice.payment_intent)
#     except stripe.error.StripeError as ex:
#         logger.error(str(ex))
#         raise Exception("Failed to get payment intent from Stripe.")

#     return stripe_payment_intent.client_secret


def _create_stripe_subscription(customer_id):
    stripe.api_key = settings.STRIPE_API_KEY

    # expand subscription's latest invoice and invoice's payment_intent
    # so we can pass it to the front end to confirm the payment
    try:
        stripe_subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                }
            ],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to create subscription on Stripe.")

    return {
        "stripe_subscription_id": stripe_subscription.id,
        "stripe_client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret,
    }


def _get_stripe_subscription(stripe_subscription_id):
    stripe.api_key = settings.STRIPE_API_KEY

    try:
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        raise Exception("Failed to get subscription from Stripe.")

    return stripe_subscription


# def _enable_subscription():
#     # create card on stripe
#     card_created = _attach_card(request.user, form.cleaned_data.get("card_token"))
#     if not card_created:
#         form.add_error(None, "Failed to add card. Please try again.")
#         return self.form_invalid(form)

#     # create subscription on stripe
#     subscription = _get_stripe_subscription(
#         request.user.stripe_customer_id, create=True
#     )

#     # update user as premium subscribed
#     if subscription and not request.user.is_premium:
#         request.user.is_premium = True
#         request.user.save()


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
    current_period_start = None
    current_period_end = None
    if request.user.stripe_subscription_id:
        subscription = _get_stripe_subscription(request.user.stripe_subscription_id)
        current_period_start = datetime.utcfromtimestamp(
            subscription["current_period_start"]
        )
        current_period_end = datetime.utcfromtimestamp(
            subscription["current_period_end"]
        )

    # update user.is_premium in case of subscription being activated directly on Stripe
    if request.user.stripe_subscription_id and not request.user.is_premium:
        request.user.is_premium = True
        request.user.save()

    # update user.is_premium if subscription has been canceled directly on Stripe
    if not request.user.stripe_subscription_id:
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
    """
    View that creates a payment intent and renders the card form on GET.
    Accepts
    """

    form_class = forms.StripeForm
    template_name = "main/billing_card.html"
    success_url = reverse_lazy("billing_index")
    success_message = "new card added"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        return context

    def get(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_API_KEY

        if not request.user.stripe_subscription_id:
            data = _create_stripe_subscription(request.user.stripe_customer_id)
            request.user.stripe_subscription_id = data["stripe_subscription_id"]
            request.user.save()

        context = self.get_context_data()
        context["stripe_client_secret"] = data["stripe_client_secret"]

        url = f"{util.get_protocol()}//{settings.CANONICAL_HOST}"
        url += reverse_lazy("billing_welcome")
        context["stripe_return_url"] = url

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
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
        subscription = _get_stripe_subscription(request.user.stripe_customer_id)
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

        subscription = _get_stripe_subscription(request.user.stripe_customer_id)
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

        subscription = _get_stripe_subscription(request.user.stripe_customer_id)
        if subscription:
            request.user.is_premium = True
            request.user.save()
        messages.success(request, "premium subscription enabled")
        return redirect("billing_index")


@login_required
def billing_welcome(request):
    """
    View that Stripe returns to if subscription initialisation is successful.
    Adds a message alert and redirects to billing_index.
    """
    payment_intent = request.GET.get("payment_intent")

    stripe.api_key = settings.STRIPE_API_KEY
    stripe_intent = stripe.PaymentIntent.retrieve(payment_intent)

    if stripe_intent["status"] == "succeeded":
        messages.success(request, "premium subscription enabled")
    elif stripe_intent["status"] == "processing":
        messages.info(request, "payment is currently processing")
    else:
        messages.error(
            request,
            "something is wrong. don't sweat it, worst case you get a premium for free",
        )

    return redirect("billing_index")


def billing_stripe_webhook(request):
    # https://stripe.com/docs/webhooks
    # possible events:
    #   * payment_intent.succeeded
    return HttpResponse()
