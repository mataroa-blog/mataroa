from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from main import models


class Command(BaseCommand):
    help = "Enqueue new post notification records"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Enqueuing notifications started."))

        yesterday = timezone.now() - timedelta(days=1)
        posts = models.Post.objects.filter(published_at__isnull=False).exclude(
            published_at__lt=yesterday
        )

        # for every post that was published today
        for p in posts:
            # ignore blog if notifications are not on
            if not p.owner.notifications_on:
                continue

            # get all active subscriber emails
            notification_list = models.Notification.objects.filter(
                blog_user=p.owner, is_active=True
            )

            for notification in notification_list:
                # verify subscriber has not already been notified
                if models.NotificationRecord.objects.filter(
                    notification=notification,
                    post=p,
                    sent_at__isnull=False,
                ).exists():
                    continue

                # create actual notification record, i.e. enqueue it
                _, created = models.NotificationRecord.objects.get_or_create(
                    notification=notification, post=p, sent_at=None
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Adding notification record for '{p.title}' to '{notification.email}'"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Exists for '{p.title}' to '{notification.email}'"
                        )
                    )

            self.stdout.write(self.style.SUCCESS(f"Enqueuing complete for '{p.title}'"))

        self.stdout.write(self.style.NOTICE("Enqueuing finished."))
