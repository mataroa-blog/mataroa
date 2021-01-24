from django.core.management.base import BaseCommand
from django.utils import timezone

from main import models


class Command(BaseCommand):
    help = "Enqueue new post notification records"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Enqueuing notifications started."))

        today = timezone.now().date()
        posts = models.Post.objects.filter(published_at=today)

        # for every post that was published today
        for p in posts:

            # ignore if notifications are not on for this blog
            if not p.owner.notifications_on:
                continue

            # get all subscriber emails
            notification_list = models.Notification.objects.filter(blog_user=p.owner)
            for notification in notification_list:

                # check if subscriber has already been notified
                if models.NotificationRecord.objects.filter(
                    notification=notification,
                    post=p,
                    sent_at__isnull=False,
                ).exists():
                    continue

                models.NotificationRecord.objects.get_or_create(
                    notification=notification, post=p, sent_at=None
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Adding notification record for '{p.title}' to '{notification.email}'"
                    )
                )

            self.stdout.write(self.style.SUCCESS(f"Enqueuing complete for '{p.title}'"))

        self.stdout.write(self.style.NOTICE("Enqueuing finished."))
