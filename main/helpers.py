import uuid

from django.utils.text import slugify

from main import models


def is_disallowed(username):
    disallowed_usernames = [
        "about",
        "abuse",
        "account",
        "accounts",
        "admin",
        "administration",
        "administrator",
        "api",
        "auth",
        "authentication",
        "billing",
        "blog",
        "blogs",
        "cdn",
        "config",
        "contact",
        "dashboard",
        "docs",
        "documentation",
        "help",
        "helpcenter",
        "home",
        "image",
        "images",
        "img",
        "index",
        "knowledgebase",
        "legal",
        "login",
        "logout",
        "pricing",
        "privacy",
        "profile",
        "random",
        "register",
        "registration",
        "search",
        "settings",
        "setup",
        "signin",
        "signup",
        "smtp",
        "static",
        "support",
        "terms",
        "test",
        "tests",
        "tmp",
        "wiki",
        "www",
    ]
    return username in disallowed_usernames


def get_post_slug(post_title, owner):
    slug = slugify(post_title)
    if models.Post.objects.filter(owner=owner, slug=slug).exists():
        slug += "-" + str(uuid.uuid4())[:8]
    return slug
