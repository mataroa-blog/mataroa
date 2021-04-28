from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from main import models, util


def get_mail_connection():
    """Returns the default EmailBackend but instantiated with a custom host."""
    return mail.get_connection(
        "django.core.mail.backends.smtp.EmailBackend",
        host=settings.EMAIL_HOST_BROADCASTS,
    )


def get_email_body(post, notification):
    """Returns the email body (which contains the post body) along with titles and links."""
    post_url = util.get_protocol() + post.get_proper_url()
    unsubscribe_url = util.get_protocol() + notification.get_unsubscribe_url()
    blog_title = post.owner.blog_title or post.owner.username

    body = f"{blog_title} has published a new blog post titled:\n{post.title}\n"
    body += "\n"
    body += f"Find the complete text at:\n{post_url}\n"
    body += "\n"
    body += "Or read it below:\n"
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


def get_email(post, notification):
    """Returns the email object, containing all info needed to be sent."""
    blog_title = post.owner.blog_title or post.owner.username
    unsubscribe_url = util.get_protocol() + notification.get_unsubscribe_url()
    body = get_email_body(post, notification)
    email = mail.EmailMessage(
        subject=post.title,
        body=body,
        from_email=f"{blog_title} <{post.owner.username}@{settings.EMAIL_FROM_HOST}>",
        to=[notification.email],
        reply_to=[post.owner.email],
        headers={
            "X-PM-Message-Stream": "newsletters",
            "List-Unsubscribe": unsubscribe_url,
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
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

        # list of messages to sent out
        message_list = []

        # get all notification records without sent_at
        # which means they have not been sent out already
        notification_records = models.NotificationRecord.objects.filter(sent_at=None)
        for record in notification_records:

            # don't send, if blog hasn't turned notifications off
            if not record.post.owner.notifications_on:
                # TODO: cancel queued record
                continue

            # don't send, if post publication date is not the day before
            yesterday = timezone.now().date() - timedelta(days=1)
            if record.post.published_at != yesterday:
                # TODO: cancel queued record
                continue

            # don't send, if email was unsubscribed since records were enqueued
            if not record.notification.is_active:
                continue

            # add email object to list
            email = get_email(record.post, record.notification)
            message_list.append(email)

            # log time email was added to the send-out list
            # ideally we would like to log when each one was sent
            # which is infeasible given the mass send strategy of newsletters
            record.sent_at = timezone.now()
            record.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Adding notification record for '{record.post.title}' to '{record.notification.email}'"
                )
            )

        # sent out messages
        connection = get_mail_connection()
        connection.send_messages(message_list)
        self.stdout.write(
            self.style.SUCCESS(f"Broadcast sent. Total {len(message_list)} emails.")
        )
