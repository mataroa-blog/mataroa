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


def prepend_frontmatter(body, post_title, pub_date):
    frontmatter = "+++\n"
    frontmatter += f'title = "{post_title}"\n'
    frontmatter += f"date = {pub_date}\n"
    frontmatter += 'template = "post.html"\n'
    frontmatter += "+++\n"
    frontmatter += "\n"

    return frontmatter + body
