from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from main import models


class PostSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def __init__(self, user, subdomain):
        self.user = user
        self.subdomain = subdomain

        models.AnalyticPage.objects.create(user=user, path="sitemap.xml")

    def items(self):
        return models.Post.objects.filter(
            owner__username=self.subdomain,
            published_at__isnull=False,
            published_at__lte=timezone.now().date(),
        )

    def location(self, obj):
        return reverse("post_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def __init__(self, user, subdomain):
        self.user = user
        self.subdomain = subdomain

        models.AnalyticPage.objects.create(user=user, path="sitemap.xml")

    def items(self):
        return models.Page.objects.filter(
            owner__username=self.subdomain, is_hidden=False
        )

    def location(self, obj):
        return reverse("page_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at
