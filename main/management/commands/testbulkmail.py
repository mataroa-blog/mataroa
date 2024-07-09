from django.conf import settings
from django.core import mail
from django.core.management.base import BaseCommand


def get_mail_connection():
    return mail.get_connection(
        "django.core.mail.backends.smtp.EmailBackend",
        host=settings.EMAIL_HOST_BROADCASTS,
    )


def get_email_body():
    body = """The need for webrings stemmed during the 90s when there was no
Google and search engines were inefficient in helping people
discover web content.

The need re-arises in 2020, when search engines are influenced by SEO
techniques and content platforms have become silos. These days, an indie
web revival would be incredible.

A webring has a specific theme, and the links that comprise it are
curated. Manually curating a webring's content means that it has been
agreed that the website's content is relevant to the webring's theme.
The modern web approach would be to add a neural network to figure out
the website's theme, but that would be totally not fly!
"""

    return body


def get_email(address):
    email = mail.EmailMessage(
        subject="Hey, this is a test",
        body=get_email_body(),
        from_email=f"Mataroa Test Agency <testing@{settings.EMAIL_FROM_HOST}>",
        to=[address],
    )
    return email


class Command(BaseCommand):
    help = "Sends a few bulk emails to test email provider."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Processing test bulk mails."))

        if not settings.EMAIL_TEST_RECEIVE_LIST:
            self.stdout.write(
                self.style.NOTICE("Setting EMAIL_TEST_RECEIVE_LIST not set.")
            )
            return

        message_list = []
        for address in settings.EMAIL_TEST_RECEIVE_LIST.split(","):
            email = get_email(address)
            message_list.append(email)

            msg = f"Logging record for '{address}'."
            self.stdout.write(self.style.SUCCESS(msg))

        connection = get_mail_connection()
        # sent out messages
        count = connection.send_messages(message_list)
        self.stdout.write(
            self.style.SUCCESS(
                f"Test broadcast sent. Total {count}/{len(message_list)} emails."
            )
        )
