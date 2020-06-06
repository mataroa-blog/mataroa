from django.contrib.syndication.views import Feed
from django.http import Http404

from main import models


class RSSBlogFeed(Feed):
    title = ""
    link = ""
    description = ""
    subdomain = ""

    def __call__(self, request, *args, **kwargs):
        if not hasattr(request, "subdomain"):
            raise Http404()
        user = models.User.objects.get(username=request.subdomain)
        self.title = user.blog_title
        self.description = user.blog_byline
        self.subdomain = request.subdomain
        return super(RSSBlogFeed, self).__call__(request, *args, **kwargs)

    def items(self):
        return models.Post.objects.filter(owner__username=self.subdomain).order_by(
            "-created_at"
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.as_markdown()

    def item_pubdate(self, item):
        return item.created_at
