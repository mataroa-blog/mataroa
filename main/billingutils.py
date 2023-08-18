import logging
from datetime import datetime

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


def attach_card(user, card_token):
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


def get_subscription(stripe_customer_id, create=False):
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


def get_payment_methods(stripe_customer_id):
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


def get_invoices(stripe_customer_id):
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


def cancel_subscription(user):
    subscription = get_subscription(user.stripe_customer_id)
    try:
        stripe.Subscription.delete(subscription["id"])
    except stripe.error.StripeError as ex:
        logger.error(str(ex))
        return Exception("Subscription could not be canceled.")
    user.is_premium = False
    user.save()
    return
