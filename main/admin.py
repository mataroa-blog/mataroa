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
                    "custom_domain",
                    "custom_domain_cert",
                    "custom_domain_key",
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


admin.site.register(models.Page, PageAdmin)


class ImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "extension",
        "owner",
        "uploaded_at",
        "data",
    )


admin.site.register(models.Image, ImageAdmin)


class AnalyticAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "created_at",
        "referer",
    )


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


admin.site.register(models.Comment, CommentAdmin)


class PostNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "blog_user",
        "unsubscribe_key",
    )


admin.site.register(models.PostNotification, PostNotificationAdmin)


class PostNotificationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sent_at",
        "post_notification",
    )


admin.site.register(models.PostNotificationRecord, PostNotificationRecordAdmin)
