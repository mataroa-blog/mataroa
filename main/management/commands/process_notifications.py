from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from main import helpers, models


def get_email_body(post, post_notification):
    post_url = helpers.get_protocol() + post.get_absolute_url()
    unsubscribe_url = helpers.get_protocol() + post_notification.get_unsubscribe_url()

    body = (
        f"{post.owner.blog_title} has published a new blog post titled: {post.title}\n"
    )
    body += "\n"
    body += f"You can find the complete text at:\n{post_url}\n"
    body += "\n"
    body += "# " + post.title + "\n"
    body += "\n"
    body += post.body + "\n"
    body += "\n"
    body += "---\n"
    body += "\n"
    body += f"Read at {post_url}\n"
    body += "\n"
    body += "---\n"
    body += "\n"
    body += "To unsubscribe click at:\n"
    body += unsubscribe_url + "\n"

    return body


class Command(BaseCommand):
    help = "Processes new posts and sends email to subscribers"

    def handle(self, *args, **options):
        # if timezone.now().hour != 13:
        #    self.stdout.write(self.style.NOTICE("No action. Current UTC is not 13:00."))
        #    return

        yesterday = timezone.now().date() - timedelta(days=1)
        posts = models.Post.objects.filter(published_at=yesterday)

        # for every post that was published yesterday
        for p in posts:
            if p.owner.notifications_on:  # if notifications_on for this blog

                # get all subscriber emails
                subscribers = models.PostNotification.objects.filter(blog_user=p.owner)
                for s in subscribers:

                    # check if subscriber has already been notified
                    if models.PostNotificationRecord.objects.filter(
                        post_notification=s, post=p, sent_at__isnull=False,
                    ).exists():
                        continue

                    record, _ = models.PostNotificationRecord.objects.get_or_create(
                        post_notification=s, post=p, sent_at=None,
                    )

                    subject = f"{p.owner.blog_title} new post publication: {p.title}"
                    body = get_email_body(p, s)
                    send_mail(
                        subject, body, settings.NOTIFICATIONS_FROM_EMAIL, [s.email],
                    )
                    record.sent_at = timezone.now()
                    record.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent post notification '{p.title}' at '{s.email}'"
                        )
                    )
