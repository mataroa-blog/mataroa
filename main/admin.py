from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjUserAdmin

from main import models


class UserAdmin(DjUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "date_joined",
        "last_login",
        "blog_title",
        "blog_byline",
        "custom_domain",
    )

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
                    "webring_name",
                    "webring_prev_url",
                    "webring_next_url",
                ),
            },
        ),
    )

    ordering = ["-id"]


admin.site.register(models.User, UserAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "owner",
        "created_at",
        "updated_at",
        "published_at",
    )

    ordering = ["-id"]


admin.site.register(models.Post, PostAdmin)


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


admin.site.register(models.Page, PageAdmin)


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


admin.site.register(models.Image, ImageAdmin)


class AnalyticAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "created_at",
    )

    ordering = ["-id"]


admin.site.register(models.Analytic, AnalyticAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "name",
        "email",
        "body",
        "created_at",
    )

    ordering = ["-id"]


admin.site.register(models.Comment, CommentAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "blog_user",
        "unsubscribe_key",
        "is_active",
    )

    ordering = ["-id"]


admin.site.register(models.Notification, NotificationAdmin)


class NotificationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sent_at",
        "notification",
        "post",
    )

    ordering = ["-id"]


admin.site.register(models.NotificationRecord, NotificationRecordAdmin)
