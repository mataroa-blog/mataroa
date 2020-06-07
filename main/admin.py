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
