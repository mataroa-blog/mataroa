import io
import uuid
import zipfile
from datetime import datetime
from string import Template

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from main import models, util


def prepend_zola_frontmatter(body, post_title, pub_date):
    frontmatter = "+++\n"
    frontmatter += f'title = "{post_title}"\n'
    frontmatter += f"date = {pub_date}\n"
    frontmatter += 'template = "post.html"\n'
    frontmatter += "+++\n"
    frontmatter += "\n"

    return frontmatter + body


def prepend_hugo_frontmatter(body, post_title, pub_date):
    frontmatter = "+++\n"
    frontmatter += f'title = "{post_title}"\n'
    frontmatter += f"date = {pub_date}\n"
    frontmatter += "+++\n"
    frontmatter += "\n"

    return frontmatter + body


def export_index(request):
    return render(request, "main/export_index.html")


@login_required
def export_markdown(request):
    if request.method == "POST":
        # get all user posts and add them into export_posts encoded
        posts = models.Post.objects.filter(owner=request.user)
        export_posts = []
        for p in posts:
            pub_date = p.published_at or p.created_at
            title = p.slug + ".md"
            body = f"# {p.title}\n\n"
            body += f"> Published on {pub_date.strftime('%b %-d, %Y')}\n\n"
            body += f"{p.body}\n"
            export_posts.append((title, io.BytesIO(body.encode())))

        # create zip archive in memory
        export_name = "export-markdown-" + str(uuid.uuid4())[:8]
        container_dir = f"{request.user.username}-mataroa-blog"
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as export_archive:
            for file_name, data in export_posts:
                export_archive.writestr(
                    export_name + f"/{container_dir}/" + file_name, data.getvalue()
                )

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={export_name}.zip"
        return response


@login_required
def export_zola(request):
    if request.method == "POST":
        # load zola templates
        with open("./export_base_zola/config.toml", "r") as zola_config_file:
            zola_config = (
                zola_config_file.read()
                .replace("example.com", f"{request.user.username}.mataroa.blog")
                .replace("Example blog title", f"{request.user.username} blog")
                .replace(
                    "Example blog description", f"{request.user.blog_byline or ''}"
                )
            )
        with open("./export_base_zola/style.css", "r") as zola_styles_file:
            zola_styles = zola_styles_file.read()
        with open("./export_base_zola/index.html", "r") as zola_index_file:
            zola_index = zola_index_file.read()
        with open("./export_base_zola/post.html", "r") as zola_post_file:
            zola_post = zola_post_file.read()
        with open("./export_base_zola/_index.md", "r") as zola_content_index_file:
            zola_content_index = zola_content_index_file.read()

        # get all user posts and add them into export_posts encoded
        posts = models.Post.objects.filter(owner=request.user)
        export_posts = []
        for p in posts:
            pub_date = p.published_at or p.created_at.date()
            title = p.slug + ".md"
            body = prepend_zola_frontmatter(
                p.body, util.escape_quotes(p.title), pub_date
            )
            export_posts.append((title, io.BytesIO(body.encode())))

        # create zip archive in memory
        export_name = "export-zola-" + str(uuid.uuid4())[:8]
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as export_archive:
            export_archive.writestr(export_name + "/config.toml", zola_config)
            export_archive.writestr(export_name + "/static/style.css", zola_styles)
            export_archive.writestr(export_name + "/templates/index.html", zola_index)
            export_archive.writestr(export_name + "/templates/post.html", zola_post)
            export_archive.writestr(
                export_name + "/content/_index.md", zola_content_index
            )
            for file_name, data in export_posts:
                export_archive.writestr(
                    export_name + "/content/" + file_name, data.getvalue()
                )

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={export_name}.zip"
        return response


@login_required
def export_hugo(request):
    if request.method == "POST":
        # load hugo templates
        with open("./export_base_hugo/config.toml", "r") as hugo_config_file:
            blog_title = request.user.blog_title or f"{request.user.username} blog"
            blog_byline = request.user.blog_byline or ""
            hugo_config = (
                hugo_config_file.read()
                .replace("example.com", f"{request.user.username}.mataroa.blog")
                .replace("Example blog title", blog_title)
                .replace("Example blog description", blog_byline)
            )
        with open("./export_base_hugo/theme.toml", "r") as hugo_theme_file:
            hugo_theme = hugo_theme_file.read()
        with open("./export_base_hugo/style.css", "r") as hugo_styles_file:
            hugo_styles = hugo_styles_file.read()
        with open("./export_base_hugo/single.html", "r") as hugo_single_file:
            hugo_single = hugo_single_file.read()
        with open("./export_base_hugo/list.html", "r") as hugo_list_file:
            hugo_list = hugo_list_file.read()
        with open("./export_base_hugo/index.html", "r") as hugo_index_file:
            hugo_index = hugo_index_file.read()
        with open("./export_base_hugo/baseof.html", "r") as hugo_baseof_file:
            hugo_baseof = hugo_baseof_file.read()

        # get all user posts and add them into export_posts encoded
        posts = models.Post.objects.filter(owner=request.user)
        export_posts = []
        for p in posts:
            title = p.slug + ".md"
            pub_date = p.published_at or p.created_at.date()
            body = prepend_hugo_frontmatter(
                p.body, util.escape_quotes(p.title), pub_date
            )
            export_posts.append((title, io.BytesIO(body.encode())))

        # create zip archive in memory
        export_name = "export-hugo-" + str(uuid.uuid4())[:8]
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as export_archive:
            export_archive.writestr(export_name + "/config.toml", hugo_config)
            export_archive.writestr(
                export_name + "/themes/mataroa/theme.toml", hugo_theme
            )
            export_archive.writestr(
                export_name + "/themes/mataroa/static/style.css", hugo_styles
            )
            export_archive.writestr(
                export_name + "/themes/mataroa/layouts/index.html", hugo_index
            )
            export_archive.writestr(
                export_name + "/themes/mataroa/layouts/_default/single.html",
                hugo_single,
            )
            export_archive.writestr(
                export_name + "/themes/mataroa/layouts/_default/list.html", hugo_list
            )
            export_archive.writestr(
                export_name + "/themes/mataroa/layouts/_default/baseof.html",
                hugo_baseof,
            )
            for file_name, data in export_posts:
                export_archive.writestr(
                    export_name + "/content/" + file_name, data.getvalue()
                )

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={export_name}.zip"
        return response


def export_unsubscribe_key(request, unsubscribe_key):
    if models.User.objects.filter(export_unsubscribe_key=unsubscribe_key).exists():
        user = models.User.objects.get(export_unsubscribe_key=unsubscribe_key)
        user.mail_export_on = False
        user.export_unsubscribe_key = uuid.uuid4()
        user.save()
        return render(
            request,
            "main/export_unsubscribe_success.html",
            {
                "blog_user": request.blog_user,
                "unsubscribed": True,
                "email": user.email,
            },
        )
    else:
        return render(
            request,
            "main/export_unsubscribe_success.html",
            {
                "blog_user": request.blog_user,
                "unsubscribed": False,
            },
        )


@login_required
def export_print(request):
    return render(
        request,
        "main/export_print.html",
        {
            "posts": models.Post.objects.filter(owner=request.user).order_by(
                "-published_at"
            ),
        },
    )


def _get_epub_author(blog_user):
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{blog_user.username}</title>
</head>
<body>
<h1>About the Author</h1>
<p>{blog_user.about_as_html}</p>
</body>
</html>
"""


def _get_epub_titlepage(blog_user):
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{blog_user.blog_title}</title>
</head>
<body>
<h1>{blog_user.blog_title}</h1>
<p>{blog_user.blog_byline}</p>
<br/>
<p>~{blog_user.username}</p>
</body>
</html>
"""


def _get_epub_chapter(post):
    chapter_body = post.body_as_html

    # process image urls
    image_url_like = util.get_protocol() + "//" + settings.CANONICAL_HOST + "/images/"
    if image_url_like in chapter_body:
        chapter_body = chapter_body.replace(image_url_like, "images/")

    # xhtml replacements
    chapter_body = chapter_body.replace("<br>", "<br/>").replace("<hr>", "<hr/>")
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{post.title}</title>
</head>
<body>
<h2>{post.title}</h2>
{chapter_body}
</body>
</html>
"""


@require_POST
@login_required
def export_epub(request):
    if request.method == "POST":
        # create uuid
        epub_uuid = str(uuid.uuid4())

        # load mimetype and container.xml
        with open("./export_base_epub/mimetype", "r") as mimetype_file:
            mimetype_content = mimetype_file.read()
        with open("./export_base_epub/container.xml", "r") as container_xml_file:
            container_xml_content = container_xml_file.read()

        # process posts
        posts = models.Post.objects.filter(owner=request.user)
        content_chapters = []
        for index, p in enumerate(posts):
            chapter = {
                "body": _get_epub_chapter(p),
                "title": p.title,
                "id": index + 1,  # +1 because we want to start from 1
                "link": f"{str(index + 1)}.xhtml",
            }
            content_chapters.append(chapter)

        # process content.opf
        content_opf_manifest = ""
        content_opf_spine = ""
        for chapter in content_chapters:
            content_opf_manifest += (
                f'    <item id="{chapter["id"]}" href="{chapter["link"]}"'
                + ' media-type="application/xhtml+xml"/>'
                + "\n"
            )
            content_opf_spine += f'    <itemref idref="{chapter["id"]}"/>' + "\n"
        with open("./export_base_epub/content.opf", "r") as opf_content_file:
            content_opf_content = opf_content_file.read()

            content_opf_content = content_opf_content.replace(
                "<dc:title></dc:title>",
                f"<dc:title>{request.user.blog_title}</dc:title>",
            )
            content_opf_content = content_opf_content.replace(
                '<dc:creator opf:role="aut"></dc:creator>',
                f'<dc:creator opf:role="aut">{request.user.username}</dc:creator>',
            )
            content_opf_content = content_opf_content.replace(
                "<dc:language></dc:language>", "<dc:language>en</dc:language>"
            )
            content_opf_content = content_opf_content.replace(
                "<dc:publisher></dc:publisher>",
                f"<dc:publisher>{request.user.username}</dc:publisher>",
            )
            content_opf_content = content_opf_content.replace(
                '<dc:identifier opf:scheme="UUID"></dc:identifier>',
                f'<dc:identifier opf:scheme="UUID">{epub_uuid}</dc:identifier>',
            )
            content_opf_content = content_opf_content.replace(
                "<dc:date></dc:date>",
                f"<dc:date>{datetime.now().date().isoformat()}</dc:date>",
            )

            content_opf_content = content_opf_content.replace(
                "<!-- manifest items -->", content_opf_manifest
            )
            content_opf_content = content_opf_content.replace(
                "<!-- spine items -->", content_opf_spine
            )

        # process toc.xhtml
        toc_xhtml_body = ""
        for chapter in content_chapters:
            toc_xhtml_body += (
                f'      <li><a href="{chapter["link"]}">{chapter["title"]}</a></li>'
                + "\n"
            )
        with open("./export_base_epub/toc.xhtml", "r") as toc_xhtml_file:
            toc_xhtml_content = toc_xhtml_file.read()
            toc_xhtml_content = toc_xhtml_content.replace(
                "<!-- chapters list -->", toc_xhtml_body
            )

        # process toc.ncx
        toc_ncx_body = ""
        toc_ncx_html_item = Template(
            """    <navPoint id="$chapter_id" playOrder="$chapter_playorder">
      <navLabel><text>$chapter_title</text></navLabel>
      <content src="$chapter_link"/>
    </navPoint>
"""
        )
        for chapter in content_chapters:
            new_item = toc_ncx_html_item.substitute(
                chapter_id=chapter["id"],
                chapter_playorder=chapter["id"] + 2,  # +2 because of title+toc
                chapter_title=chapter["title"],
                chapter_link=chapter["link"],
            )
            toc_ncx_body += new_item + "\n"
        toc_ncx_body += toc_ncx_html_item.substitute(
            chapter_id="author",
            chapter_playorder=len(content_chapters) + 3,
            chapter_title="About the Author",
            chapter_link="author.xhtml",
        )
        with open("./export_base_epub/toc.ncx", "r") as toc_ncx_file:
            toc_ncx_content = toc_ncx_file.read()

            toc_ncx_content = toc_ncx_content.replace(
                "<text></text>",
                f"<text>{request.user.blog_title}</text>",
            )
            toc_ncx_content = toc_ncx_content.replace(
                '<meta name="dtb:uid" content=""/>',
                f'<meta name="dtb:uid" content="{epub_uuid}"/>',
            )
            toc_ncx_content = toc_ncx_content.replace(
                "<!-- nav points -->", toc_ncx_body
            )

        # create zip archive in memory
        export_name = "export-book-" + epub_uuid[:8]
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as export_archive:
            # write meta pages
            export_archive.writestr("mimetype", mimetype_content)
            export_archive.writestr("META-INF/container.xml", container_xml_content)
            export_archive.writestr("OEBPS/content.opf", content_opf_content)
            export_archive.writestr("OEBPS/toc.xhtml", toc_xhtml_content)
            export_archive.writestr("OEBPS/toc.ncx", toc_ncx_content)

            # write post / chapter  files
            for chapter in content_chapters:
                export_archive.writestr(f'OEBPS/{chapter["link"]}', chapter["body"])

            # write images
            for img in models.Image.objects.filter(owner=request.user):
                export_archive.writestr(f"OEBPS/images/{img.filename}", img.data)

            # write title and author page
            export_archive.writestr(
                "OEBPS/titlepage.xhtml", _get_epub_titlepage(request.user)
            )
            export_archive.writestr(
                "OEBPS/author.xhtml", _get_epub_author(request.user)
            )

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/epub")
        response["Content-Disposition"] = f"attachment; filename={export_name}.epub"
        return response
