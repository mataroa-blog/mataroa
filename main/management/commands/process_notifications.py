from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from main import helpers, models


def get_mail_connection():
    return mail.get_connection(
        "django.core.mail.backends.smtp.EmailBackend",
        host=settings.EMAIL_HOST_BROADCASTS,
    )


def get_email_body(post, notification):
    post_url = helpers.get_protocol() + post.get_proper_url()
    # unsubscribe_url = helpers.get_protocol() + notification.get_unsubscribe_url()
    blog_title = post.owner.blog_title or post.owner.username

    body = f"{blog_title} has published a new blog post titled: {post.title}\n"
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
    # body += "To unsubscribe click at:\n"
    # body += unsubscribe_url + "\n"

    return body


def get_email(post, notification):
    blog_title = post.owner.blog_title or post.owner.username
    subject = f"{blog_title} new post publication: {post.title}"
    # unsubscribe_url = helpers.get_protocol() + notification.get_unsubscribe_url()
    body = get_email_body(post, notification)
    email = mail.EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.NOTIFICATIONS_FROM_EMAIL,
        to=[notification.email],
        reply_to=[post.owner.email],
        headers={
            "X-PM-Message-Stream": "newsletters",
            # "List-Unsubscribe": unsubscribe_url,
            # "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )
    return email


class Command(BaseCommand):
    help = "Processes new posts and sends email to subscribers"

    def handle(self, *args, **options):
        if timezone.now().hour != 13:
            self.stdout.write(self.style.NOTICE("No action. Current UTC is not 13:00."))
            return

        self.stdout.write(self.style.NOTICE("Processing notifications."))

        yesterday = timezone.now().date() - timedelta(days=1)
        posts = models.Post.objects.filter(published_at=yesterday)

        connection = get_mail_connection()

        # for every post that was published yesterday
        for p in posts:

            # ignore if notifications are not on for this blog
            if not p.owner.notifications_on:
                continue

            # list of messages
            message_list = []

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

                record, _ = models.NotificationRecord.objects.get_or_create(
                    notification=notification, post=p, sent_at=None
                )

                email = get_email(p, notification)
                message_list.append(email)

                record.sent_at = timezone.now()
                record.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Adding notification record for '{p.title}' to '{notification.email}'"
                    )
                )

            connection.send_messages(message_list)
            self.stdout.write(self.style.SUCCESS(f"Sent broadcast for '{p.title}'"))
