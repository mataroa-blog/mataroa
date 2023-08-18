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

from main import billingutils, forms

logger = logging.getLogger(__name__)


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
    subscription = billingutils.get_subscription(request.user.stripe_customer_id)
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
    payment_methods = billingutils.get_payment_methods(
        request.user.stripe_customer_id
    ).values()

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
            "invoice_list": billingutils.get_invoices(request.user.stripe_customer_id),
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
            card_created = billingutils.attach_card(
                request.user, form.cleaned_data.get("card_token")
            )
            if not card_created:
                form.add_error(None, "Failed to add card. Please try again.")
                return self.form_invalid(form)

            # create subscription on stripe
            subscription = billingutils.get_subscription(
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

        self.stripe_payment_methods = billingutils.get_payment_methods(
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
        stripe_payment_methods = billingutils.get_payment_methods(
            request.user.stripe_customer_id
        )

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
        try:
            billingutils.cancel_subscription(request.user)
        except Exception:
            return HttpResponse("Subscription could not be canceled.", status=503)
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

        subscription = billingutils.get_subscription(request.user.stripe_customer_id)
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

        subscription = billingutils.get_subscription(
            request.user.stripe_customer_id, create=True
        )
        if subscription:
            request.user.is_premium = True
            request.user.save()
        messages.success(request, "premium subscription enabled")
        return redirect("billing_index")
