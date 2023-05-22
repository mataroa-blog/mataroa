from django.apps import AppConfig
from django.db.models.signals import post_save


class MainConfig(AppConfig):
    name = "main"

    def ready(self):
        from main.models import Post
        from main import signals

        post_save.connect(signals.update_search_post, sender=Post)
