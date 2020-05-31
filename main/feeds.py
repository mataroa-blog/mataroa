from django.contrib.syndication.views import Feed

from main import models


class BlogFeed(Feed):
    title = ""
    link = ""
    description = ""

    def __call__(self, request, *args, **kwargs):
        user = models.User.objects.get(username=request.subdomain)
        self.title = user.blog_title
        return super(BlogFeed, self).__call__(request, *args, **kwargs)

    def items(self):
        return models.Post.objects.filter().order_by("-created_at")

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body[:100]
