import base64
import uuid

import bleach
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone

from main import helpers, validators


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="This will be your subdomain. Lowercase alphanumeric.",
        validators=[validators.AlphanumericHyphenValidator()],
        error_messages={"unique": "A user with that username already exists."},
    )
    about = models.TextField(blank=True, null=True)
    blog_title = models.CharField(max_length=500, blank=True, null=True)
    blog_byline = models.CharField(max_length=500, blank=True, null=True)
    footer_note = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        default=None,
        help_text="Supports markdown",
    )
    custom_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="DNS: CNAME your .mataroa.blog subdomain or A with IP 95.217.176.64",
        validators=[validators.validate_domain_name],
    )
    comments_on = models.BooleanField(
        default=False,
        help_text="Enable/disable comments for your blog",
    )
    notifications_on = models.BooleanField(
        default=False,
        help_text="Allow/disallow people subscribing for new posts notifications",
    )

    # webring related
    webring_name = models.CharField(max_length=200, blank=True, null=True)
    webring_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webring info URL",
        help_text="Informational URL.",
    )
    webring_prev_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webring previous URL",
        help_text="URL for your webring's previous website.",
    )
    webring_next_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webring next URL",
        help_text="URL for your webring's next website.",
    )

    class Meta:
        ordering = ["-id"]

    @property
    def footer_note_as_html(self):
        return helpers.md_to_html(self.footer_note)

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
        help_text="Leave blank to keep as draft/unpublished. Use a future date for auto-posting.",
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        unique_together = [["slug", "owner"]]

    @property
    def body_as_html(self):
        return helpers.md_to_html(self.body)

    @property
    def body_as_text(self):
        as_html = helpers.md_to_html(self.body)
        return bleach.clean(as_html, strip=True, tags=[])

    @property
    def is_published(self):
        if not self.published_at:
            # draft case
            return False
        if self.published_at > timezone.now().date():
            # future publishing date case
            return False
        return True

    def get_absolute_url(self):
        path = reverse("post_detail", kwargs={"slug": self.slug})
        return f"//{self.owner.username}.{settings.CANONICAL_HOST}{path}"

    def get_proper_url(self):
        """Returns custom domain URL if custom_domain exists, else subdomain URL."""
        if self.owner.custom_domain:
            path = reverse("post_detail", kwargs={"slug": self.slug})
            return f"//{self.owner.custom_domain}{path}"
        else:
            return get_absolute_url(self)

    def __str__(self):
        return self.title


class Image(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=300)  # original filename
    slug = models.CharField(max_length=300, unique=True)
    data = models.BinaryField()
    extension = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    @property
    def filename(self):
        return self.slug + "." + self.extension

    @property
    def data_as_base64(self):
        return base64.b64encode(self.data).decode("utf-8")

    @property
    def raw_url_absolute(self):
        path = reverse(
            "image_raw", kwargs={"slug": self.slug, "extension": self.extension}
        )
        return f"//{settings.CANONICAL_HOST}{path}"

    def get_absolute_url(self):
        path = reverse("image_detail", kwargs={"slug": self.slug})
        return f"//{settings.CANONICAL_HOST}{path}"

    def __str__(self):
        return self.name


class Page(models.Model):
    title = models.CharField(max_length=300)
    slug = models.CharField(
        max_length=300,
        validators=[validators.AlphanumericHyphenValidator()],
        help_text="Lowercase letters, numbers, and - (hyphen) allowed.",
    )
    body = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_hidden = models.BooleanField(
        default=False,
        help_text="If checked, page link will not appear on index footer.",
    )

    class Meta:
        ordering = ["slug"]
        unique_together = [["slug", "owner"]]

    @property
    def body_as_html(self):
        return helpers.md_to_html(self.body)

    def get_absolute_url(self):
        path = reverse("page_detail", kwargs={"slug": self.slug})
        return f"//{self.owner.username}.{settings.CANONICAL_HOST}{path}"

    def __str__(self):
        return self.title


class Analytic(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    referer = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.created_at.strftime("%c") + ": " + self.post.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    name = models.CharField(max_length=150, default="Anonymous", null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.created_at.strftime("%c") + ": " + self.post.title


class PostNotification(models.Model):
    blog_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    email = models.EmailField()
    unsubscribe_key = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        ordering = ["email"]
        unique_together = [["email", "blog_user"]]

    def get_unsubscribe_url(self):
        domain = (
            self.blog_user.custom_domain
            or f"{self.blog_user.username}.{settings.CANONICAL_HOST}"
        )
        path = reverse("notification_unsubscribe_key", args={self.unsubscribe_key})
        return f"//{domain}{path}"

    def __str__(self):
        return self.email + " – " + str(self.unsubscribe_key)


class PostNotificationRecord(models.Model):
    post_notification = models.ForeignKey(
        PostNotification, on_delete=models.SET_NULL, null=True
    )
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True)
    sent_at = models.DateTimeField(default=timezone.now, null=True)

    class Meta:
        ordering = ["-sent_at"]
        unique_together = [["post", "post_notification"]]

    def __str__(self):
        if self.post_notification:
            return self.sent_at.strftime("%c") + " – " + self.post_notification.email
        else:
            return self.sent_at.strftime("%c") + " – NULL"
