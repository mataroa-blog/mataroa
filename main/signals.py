from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import Post


@receiver(post_save, sender=Post)
def update_search_post(sender, instance, **kwargs):
    Post.objects.filter(id=instance.id).update(
        search_post=SearchVector("title") + SearchVector("body")
    )
