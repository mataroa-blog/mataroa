import uuid

import bleach
import markdown
import pygments
from django.utils.text import slugify
from pygments.formatters import HtmlFormatter
from pygments.lexers import ClassNotFound, get_lexer_by_name, get_lexer_for_filename

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
    processed_text = ""
    within_code_block = False
    lexer = None
    code_block = ""
    for line in text.split("\n"):
        if line[:3] == "```":
            # code block backticks found, either begin or end
            if not within_code_block:
                # this is the beginning of a block
                lang = line[3:].strip()
                if lang:
                    # then this is a *code* block
                    within_code_block = True
                    lang_filename = "file." + lang
                    try:
                        lexer = get_lexer_for_filename(lang_filename)
                    except ClassNotFound:
                        lexer = get_lexer_by_name(lang)
                    except ClassNotFound:
                        # can't find lexer, just use C lang as default
                        lexer = get_lexer_by_name("c")

                    # continue because we don't want to add backticks in the processed text
                    continue
                else:
                    # no lang, so just a generic block (non-code)
                    lexer = None
            else:
                # then this is the end of a code block
                # actual highlighting happens here
                within_code_block = False
                highlighted_block = pygments.highlight(
                    code_block, lexer, HtmlFormatter(noclasses=True, cssclass="")
                )
                processed_text += highlighted_block
                code_block = ""  # reset code_block variable

                # continue because we don't want to add backticks in the processed text
                continue

        if within_code_block:
            code_block += line + "\n"
        else:
            processed_text += line + "\n"

    return processed_text


def clean_html(dirty_html):
    return bleach.clean(
        dirty_html,
        tags=[
            "a",
            "abbr",
            "acronym",
            "article",
            "b",
            "bdi",
            "bdo",
            "br",
            "blockquote",
            "cite",
            "code",
            "div",
            "dfn",
            "em",
            "kbd",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "hr",
            "i",
            "iframe",
            "img",
            "li",
            "mark",
            "ol",
            "p",
            "pre",
            "q",
            "rb",
            "rt",
            "rtc",
            "ruby",
            "s",
            "samp",
            "section",
            "small",
            "span",
            "strong",
            "sub",
            "sup",
            "time",
            "u",
            "ul",
            "var",
            "wbr",
        ],
        attributes=[
            "alt",
            "class",
            "height",
            "href",
            "id",
            "seamless",
            "src",
            "style",
            "title",
            "width",
        ],
        styles=[
            "background",
            "border",
            "border-radius",
            "color",
            "display",
            "height",
            "width",
        ],
    )


def md_to_html(markdown_string):
    dirty_html = markdown.markdown(
        syntax_highlight(markdown_string),
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
            "markdown.extensions.footnotes",
        ],
    )
    return clean_html(dirty_html)
