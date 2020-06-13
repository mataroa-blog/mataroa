import uuid

import pygments
from django.utils.text import slugify
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename

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


def syntax_highlight(text):
    """Highlights markdown codeblocks within a markdown text."""
    highlighted_text = ""
    within_codeblock = False
    lexer = None
    code_block = ""
    for line in text.split("\n"):
        if within_codeblock and lexer:
            if line[:3] == "```":
                # end of code block, highlight it now
                within_codeblock = False
                highlighted_codeblock = pygments.highlight(
                    code_block, lexer, HtmlFormatter(noclasses=True, cssclass="")
                )
                highlighted_text += highlighted_codeblock
                continue
            else:
                code_block += line
        else:
            if line[:3] != "```":
                highlighted_text += line

        if line[:3] == "```" and not within_codeblock:
            lang_ext = "file." + line[3:].strip()
            lexer = get_lexer_for_filename(lang_ext)
            within_codeblock = True

    return highlighted_text
