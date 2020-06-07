import markdown
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone

from main import validators


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="This will be your subdomain. Lowercase alphanumeric.",
        validators=[validators.StrictUsernameValidator()],
        error_messages={"unique": "A user with that username already exists."},
    )
    about = models.TextField(blank=True, null=True)
    blog_title = models.CharField(max_length=500, blank=True, null=True)
    blog_byline = models.CharField(max_length=500, blank=True, null=True)
    custom_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="DNS: CNAME your .mataroa.blog subdomain or A with IP 95.217.176.64",
        validators=[validators.validate_domain_name],
    )
    custom_domain_cert = models.TextField(blank=True, null=True)
    custom_domain_key = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("user_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return self.username


class Post(models.Model):
    title = models.CharField(max_length=300)
    slug = models.CharField(max_length=300)
    body = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateField(
        default=timezone.now,
        blank=True,
        null=True,
        help_text="Leave blank to keep as draft/unpublished",
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        unique_together = [["slug", "owner"]]

    @property
    def as_html(self):
        return markdown.markdown(
            self.body,
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.tables",
            ],
        )

    def get_absolute_url(self):
        path = reverse("post_detail", kwargs={"slug": self.slug})
        return f"//{self.owner.username}.{settings.CANONICAL_HOST}{path}"

    def __str__(self):
        return self.title
