# Code Walkthrough

Here, an overview of the project's code sources is presented.

All business logic of the application is in one Django app: [`main`](/main).

Condensed and commented sources file tree:

```
.
├── Caddyfile # configuration for Caddy webserver
├── Dockerfile
├── LICENSE
├── Makefile # make-defined tasks
├── README.md
├── backup-database.sh
├── deploy.sh
├── docker-compose.yml
├── docs/
├── export_base_hugo/ # base sources for hugo export functionality
├── export_base_zola/ # base sources for zola export functionality
├── main/
│   ├── admin.py
│   ├── apps.py
│   ├── denylist.py # list of various keywords allowed and denied
│   ├── feeds.py # django rss functionality
│   ├── forms.py
│   ├── management/ # commands under `python manage.py`
│   │   └── commands/
│   │       ├── enqueue_notifications.py
│   │       ├── populate_dev_data.py
│   │       └── process_notifications.py
│   │       └── mail_exports.py
│   ├── middleware.py # mostly subdomain routing
│   ├── migrations/
│   ├── models.py
│   ├── static/
│   ├── templates
│   │   ├── main/
│   │   ├── partials/
│   │   │   ├── drag-and-drop-upload.js
│   │   │   ├── footer.html
│   │   │   ├── footer_blog.html
│   │   │   └── webring.html
│   │   └── registration/
│   ├── tests/
│   │   ├── test_billing.py
│   │   ├── test_blog.py
│   │   ├── test_comments.py
│   │   ├── test_images.py
│   │   ├── test_management.py
│   │   ├── test_pages.py
│   │   ├── test_posts.py
│   │   ├── test_users.py
│   │   └── testdata/
│   ├── urls.py
│   ├── util.py
│   ├── validators.py # custom form and field validators
│   ├── views.py
│   ├── views_billing.py
│   └── views_export.py
├── manage.py
├── mataroa
│   ├── asgi.py
│   ├── settings.py # django configuration file
│   ├── urls.py
│   └── wsgi.py
├── pyproject.toml # only used by black formatter
├── requirements.in # user-editable requirements file
├── requirements.txt # pip-compile generated version-locked dependencies
├── requirements_dev.txt # user-editable development requirements
└── uwsgi.ini # configuration for uWSGI
```

## [`main/urls.py`](/main/urls.py)

All urls are in this module. They are visually divided into several sections:

* general, includes index, dashboard, static pages
* user system, includes signup, settings, logout
* blog posts, the CRUD opertions of
* blog extras, includes rss and newsletter features
* comments, related to the blog post comments
* billing, subscription and card related
* blog import, export, webring
* images CRUD
* analytics list and details
* pages CRUD

## [`main/views.py`](/main/views.py)

The significant majority of business logic is in the `views.py` module.

It includes:

* indexes, dashboard, static pages
* user CRUD and login/logout
* posts CRUD
* comments CRUD
* images CRUD
* pages CRUD
* webring
* analytics
* notifications subscribe/unsubscribe

Generally, [Django class-based generic views](https://docs.djangoproject.com/en/3.2/topics/class-based-views/generic-display/)
are used most of the time as they provide useful functionality abtracted away.

The Django source code [for generic views](https://github.com/django/django/tree/main/django/views/generic)
is also extremely readable:

* [base.py](https://github.com/django/django/blob/main/django/views/generic/base.py): base `View` and `TemplateView`
* [list.py](https://github.com/django/django/blob/main/django/views/generic/list.py): `ListView`
* [edit.py](https://github.com/django/django/blob/main/django/views/generic/edit.py): `UpdateView`, `DeleteView`, `FormView`
* [detail.py](https://github.com/django/django/blob/main/django/views/generic/detail.py): `DetailView`

[Function-based views](https://docs.djangoproject.com/en/3.2/intro/tutorial01/#write-your-first-view)
are used in cases where the CRUD/RESTful design pattern is not clear such as
`notification_unsubscribe_key` where we unsubscribe an email via a GET operation.

## [`main/views_export.py`](/main/views_export.py)

This module contains all views related to the export capabilities of mataroa.

The way the exports work is by reading the base files from the repository root:
([export_base_hugo](export_base_hugo/) and [export_base_zola](export_base_zola/)
for Hugo and Zola respectively. After reading, we replace some strings on the
configurations, generate posts as markdown strings, and zip-archive everything
in-memory. Finally, we respond using `application/zip` content type and
[Content-Disposition](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition)
`attachment`.

## [`main/views_billing.py`](/main/views_billing.py)

This module contains all billing and subscription related views. It’s design to
support one payment processor, Stripe.

## [`main/tests/`](/main/tests/)

All tests are under this directory. They are divided into several modules,
based on the functionality and the views they test.

Everything uses the built-in Python `unittest` module along with standard
Django testing facilities.

## [`main/models.py`](/main/models.py) and [`main/migrations/`](/main/migrations/`)

`main/models.py` is where the database schema is defined, translated into
Django ORM-speak. This always displays the latest schema.

`main/migrations/` includes all incremental migrations required to reach
the schema defined in `main/models.py`.

We use the built-in Django system to generate and execute mgirations:

The steps to make a schema change would be something like:

1. Make the change in `main/models.py`. See
[Django Model field reference](https://docs.djangoproject.com/en/3.2/ref/models/fields/).
1. Run `python manage.py makemigrations` to auto-generate the migrations.
1. Run `python manage.py migrate` to execute migrations.
1. Also `make format` before committing.
