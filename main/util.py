import io
import re
import uuid
import zipfile

import bleach
import mistletoe
from bleach.css_sanitizer import CSSSanitizer
from django.conf import settings
from django.utils.text import slugify
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name

from main import denylist, models


def is_disallowed(username):
    """Return true if username is not allowed to be registered."""
    if username[0] == "_":
        # do not allow leading underscores
        return True
    return username in denylist.DISALLOWED_USERNAMES


def get_approx_number(number):
    """Get approximate number, eg. 1823 -> 2k"""
    if number > 999:
        approx = round(number / 1000)
        return f"{approx}k"

    return number


def create_post_slug(post_title, owner, post=None):
    """
    Generate slug given post title. Optional post arg for post that already
    exists.
    """
    slug = slugify(post_title)

    # in case of post_title such as این متن است
    if not slug:
        generated_uuid = str(uuid.uuid4())[:8]
        slug = f"{generated_uuid[:3]}-{generated_uuid[3:5]}-{generated_uuid[5:]}"

    # if post is not None, then this is an update op
    if post is not None:
        post_with_same_slugs = models.Post.objects.filter(owner=owner, slug=slug)
        if post_with_same_slugs:
            if post_with_same_slugs.first().id == post.id:
                # if post being updating is the same one, then just return the same slug
                return slug
            else:
                # if post being updating is another one, then add a suffix to differentiate
                slug += "-" + str(uuid.uuid4())[:8]
                return slug

    # if post arg is None, then this is a new post
    # if slug already exists for another post, add a suffix to make it unique
    if models.Post.objects.filter(owner=owner, slug=slug).exists():
        slug += "-" + str(uuid.uuid4())[:8]

    return slug


class PygmentsRenderer(mistletoe.HTMLRenderer):
    """Highlights markdown codeblocks within a markdown text."""
    formatter = HtmlFormatter()
    formatter.noclasses = True

    def __init__(self, *extras, style='default'):
        super().__init__(*extras)
        self.formatter.style = get_style_by_name(style)

    def render_block_code(self, token):
        code = token.children[0].content
        lexer = get_lexer_by_name(token.language) if token.language else guess_lexer(code)
        return highlight(code, lexer, self.formatter)


def clean_html(dirty_html, strip_tags=False):
    """Clean potentially evil HTML.

    - strip_tags: true will strip everything, false will escape.
    """
    if strip_tags:
        return bleach.clean(dirty_html, strip=True)

    css_sanitizer = CSSSanitizer(allowed_css_properties=denylist.ALLOWED_CSS_STYLES)
    return bleach.clean(
        dirty_html,
        tags=denylist.ALLOWED_HTML_ELEMENTS,
        attributes=denylist.ALLOWED_HTML_ATTRS,
        css_sanitizer=css_sanitizer,
    )


def md_to_html(markdown_string, strip_tags=False):
    """Return HTML formatted string, given a markdown one."""
    if not markdown_string:
        return ""
    dirty_html = mistletoe.markdown(markdown_string, renderer=PygmentsRenderer)
    return clean_html(dirty_html, strip_tags)


def remove_control_chars(text):
    """Remove control characters from a string.

    We remove all characters of the Cc category of unicode, except for
    \t (tab), \n (new line), \r (carriage return).
    See http://www.unicode.org/reports/tr44/#General_Category_Values
    """
    control_char_string = "".join(denylist.DISALLOWED_CHARACTERS)
    control_char_re = re.compile("[%s]" % re.escape(control_char_string))
    return control_char_re.sub(" ", text)


def get_protocol():
    if settings.DEBUG:
        return "http:"
    else:
        return "https:"


def generate_markdown_export(user_id):
    """
    Generates a markdown export ZIP file in /tmp/.
    Returns (export name, export filepath).
    """
    # compile all posts into dictionary
    user = models.User.objects.get(id=user_id)
    user_posts = models.Post.objects.filter(owner=user)
    export_posts = []
    for p in user_posts:
        pub_date = p.published_at or p.created_at
        title = p.slug + ".md"
        body = f"# {p.title}\n\n"
        body += f"> Published on {pub_date.strftime('%b %-d, %Y')}\n\n"
        body += f"{p.body}\n"
        export_posts.append((title, io.BytesIO(body.encode())))

    # write zip archive in /tmp/
    export_name = "export-markdown-" + str(uuid.uuid4())[:8]
    container_dir = f"{user.username}-mataroa-blog"
    zip_outfile = f"/tmp/{export_name}.zip"
    with zipfile.ZipFile(
        zip_outfile, "a", zipfile.ZIP_DEFLATED, False
    ) as export_archive:
        for file_name, data in export_posts:
            export_archive.writestr(
                export_name + f"/{container_dir}/" + file_name, data.getvalue()
            )

    return (export_name, zip_outfile)


def escape_quotes(input_string):
    output_string = input_string.replace('"', '\\"')
    return output_string
