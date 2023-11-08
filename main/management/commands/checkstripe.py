import stripe
from django.conf import settings
from django.core.management.base import BaseCommand

from main import models


class Command(BaseCommand):
    help = "Check Stripe data is in sync with database."

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_API_KEY

        total_count = 0
        last = None
        while True:
            if last:
                subscription_list = stripe.Subscription.list(
                    limit=100, starting_after=last.id
                )
            else:
                subscription_list = stripe.Subscription.list(limit=100)
            total_count += len(subscription_list)
            print(f"Current total: {total_count}")

            for subscription in subscription_list:
                if not models.User.objects.filter(
                    stripe_customer_id=subscription.customer
                ).exists():
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Customer not found in mataroa "
                            "database: {subscription.customer}"
                        )
                    )

            if not subscription_list.has_more:
                break
            last = list(reversed(subscription_list))[0]
