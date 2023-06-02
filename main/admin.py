from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjUserAdmin
from django.utils.html import format_html

from main import models, util


@admin.register(models.User)
class UserAdmin(DjUserAdmin):
    list_display = (
        "id",
        "username",
        "blog_url",
        "email",
        "date_joined",
        "last_login",
        "blog_title",
        "stripe_customer_id",
        "is_premium",
        "mail_export_on",
    )
    list_display_links = ("id", "username")

    @admin.display
    def blog_url(self, obj):
        url = f"{util.get_protocol()}"
        if obj.custom_domain:
            url += f"//{obj.custom_domain}"
        else:
            url += f"//{obj.username}.{settings.CANONICAL_HOST}"
        return format_html(f'<a href="{url}">{url}</a>')

    fieldsets = DjUserAdmin.fieldsets + (
        (
            "Blog options",
            {
                "fields": (
                    "about",
                    "blog_title",
                    "blog_byline",
                    "footer_note",
                    "theme_zialucia",
                    "redirect_domain",
                    "custom_domain",
                    "comments_on",
                    "notifications_on",
                    "mail_export_on",
                    "post_backups_on",
                    "export_unsubscribe_key",
                    "webring_name",
                    "webring_prev_url",
                    "webring_next_url",
                    "stripe_customer_id",
                    "monero_address",
                    "is_premium",
                    "is_grandfathered",
                    "api_key",
                ),
            },
        ),
    )

    ordering = ["-id"]


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "post_url",
        "owner",
        "created_at",
        "updated_at",
        "published_at",
    )

    @admin.display
    def post_url(self, obj):
        url = util.get_protocol() + obj.get_proper_url()
        return format_html(f'<a href="{url}">{url}</a>')

    ordering = ["-id"]


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "owner",
        "created_at",
        "updated_at",
        "is_hidden",
    )

    ordering = ["-id"]


@admin.register(models.Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "extension",
        "owner",
        "uploaded_at",
    )

    ordering = ["-id"]


@admin.register(models.AnalyticPage)
class AnalyticPageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "path",
        "created_at",
    )

    ordering = ["-id"]


@admin.register(models.AnalyticPost)
class AnalyticPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "created_at",
    )

    ordering = ["-id"]


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "is_approved",
        "name",
        "email",
        "body",
        "created_at",
    )

    ordering = ["-id"]


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "blog_user",
        "unsubscribe_key",
        "is_active",
    )

    ordering = ["-id"]


@admin.register(models.NotificationRecord)
class NotificationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sent_at",
        "is_canceled",
        "notification",
        "post",
    )

    ordering = ["-id"]


@admin.register(models.ExportRecord)
class ExportRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "sent_at",
        "user",
    )
    list_display_links = ("id", "name")

    ordering = ["-id"]


@admin.register(models.Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "owner",
    )
    list_display_links = ("id", "title")

    ordering = ["-id"]
