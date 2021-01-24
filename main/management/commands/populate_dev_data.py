from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main import models


class Command(BaseCommand):
    help = "Populate database with development data."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Population canceled. Django settings NODEBUG is on.")

        if not models.User.objects.exists():
            raise CommandError(
                "Population canceled. There needs to exist at least one user in the database."
            )

        self.stdout.write(self.style.NOTICE("Initiating development data population."))

        # get a user
        user = models.User.objects.all().first()

        # blog settings
        user.blog_title = "sirodoht dev blog"
        user.blog_byline = "stuff"
        user.footer_note = "[Public domain](/license). Powered&nbsp;by&nbsp;[mataroa.blog](https://mataroa.blog/)."
        user.notifications_on = True
        user.webring_name = "Tech makers webring"
        user.save()

        # posts
        post_a = models.Post()
        post_a.owner = user
        post_a.title = "Hello world!"
        post_a.slug = "hello-world"
        post_a.body = "Hi there!\n\nHow are you?"
        post_a.published_at = timezone.now()
        post_a.save()

        post_b = models.Post()
        post_b.owner = user
        post_b.title = "Hi again"
        post_b.slug = "hi-again"
        post_b.body = "There are things that are within our power, and things that fall outside our power. Within our power are our own opinions, aims, desires, dislikes—in sum, our own thoughts and actions. Outside our power are our physical characteristics, the class into which we were born, our reputation in the eyes of others, and honors and offices that may be bestowed on us."
        post_b.save()

        post_draft = models.Post()
        post_draft.owner = user
        post_draft.title = "I am draft"
        post_draft.slug = "i-am-draft"
        post_draft.body = "As in I am Groot."
        post_draft.save()

        # page
        page_a = models.Page()
        page_a.owner = user
        page_a.title = "License"
        page_a.slug = "licence"
        page_a.body = "MIT"
        page_a.save()

        # notifications
        notification_a = models.Notification()
        notification_a.blog_user = user
        notification_a.email = "zf@sirodoht.com"
        notification_a.save()

        notification_b = models.Notification()
        notification_b.blog_user = user
        notification_b.email = "zf+matab@sirodoht.com"
        notification_b.save()

        # notification records
        notificationrecord_a = models.NotificationRecord()
        notificationrecord_a.notification = notification_a
        notificationrecord_a.post = post_a
        notificationrecord_a.save()

        notificationrecord_b = models.NotificationRecord()
        notificationrecord_b.notification = notification_b
        notificationrecord_b.post = post_a
        notificationrecord_b.save()

        notificationrecord_c = models.NotificationRecord()
        notificationrecord_c.notification = notification_a
        notificationrecord_c.post = post_b
        notificationrecord_c.save()

        notificationrecord_d = models.NotificationRecord()
        notificationrecord_d.notification = notification_b
        notificationrecord_d.post = post_b
        notificationrecord_d.save()

        self.stdout.write(
            self.style.SUCCESS("Development data population is complete.")
        )
