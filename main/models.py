import base64

import markdown
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

    # custom domain related
    custom_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="DNS: CNAME your .mataroa.blog subdomain or A with IP 95.217.176.64",
        validators=[validators.validate_domain_name],
    )
    custom_domain_cert = models.TextField(blank=True, null=True)
    custom_domain_key = models.TextField(blank=True, null=True)

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
        dirty_html = markdown.markdown(
            helpers.syntax_highlight(self.footer_note),
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.tables",
            ],
        )
        return helpers.clean_html(dirty_html)

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
    def as_html(self):
        dirty_html = markdown.markdown(
            helpers.syntax_highlight(self.body),
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.tables",
                "markdown.extensions.footnotes",
            ],
        )
        return helpers.clean_html(dirty_html)

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
    def as_html(self):
        dirty_html = markdown.markdown(
            helpers.syntax_highlight(self.body),
            extensions=[
                "markdown.extensions.fenced_code",
                "markdown.extensions.tables",
            ],
        )
        return helpers.clean_html(dirty_html)

    def get_absolute_url(self):
        path = reverse("page_detail", kwargs={"slug": self.slug})
        return f"//{self.owner.username}.{settings.CANONICAL_HOST}{path}"

    def __str__(self):
        return self.title
