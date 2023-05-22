from django.contrib.postgres.search import SearchVector

from main.models import Post


def update_search_post(sender, instance, **kwargs):
    Post.objects.filter(id=instance.id).update(
        search_post=SearchVector("title") + SearchVector("body")
    )
