from django.contrib import admin
from django.urls import include, path, re_path

from main import feeds, views, views_export

admin.site.site_header = "mataroa administration"

# general
urlpatterns = [
    path("", views.index, name="index"),
    path("blog/", views.blog_index, name="blog_index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("modus-operandi/", views.modus, name="modus"),
    path("premium/", views.Interest.as_view(), name="interest"),
    path("markdown-guide/", views.markdown_guide, name="markdown_guide"),
    path(
        ".well-known/acme-challenge/8Ztw4vrGMbl_ocZpth3LIjhKbnFYGwHeMym23v9CGxo",
        views.acme_challenge,
        name="acme_challenge",
    ),
]

# user system
urlpatterns += [
    path("accounts/logout/", views.Logout.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", views.UserCreate.as_view(), name="user_create"),
    path("accounts/<int:pk>/", views.UserDetail.as_view(), name="user_detail"),
    path("accounts/<int:pk>/edit/", views.UserUpdate.as_view(), name="user_update"),
    path("accounts/<int:pk>/delete/", views.UserDelete.as_view(), name="user_delete"),
]

# blog posts
urlpatterns += [
    path("blog/create/", views.PostCreate.as_view(), name="post_create"),
    path("blog/<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),
    path("blog/<slug:slug>/edit/", views.PostUpdate.as_view(), name="post_update"),
    path("blog/<slug:slug>/delete/", views.PostDelete.as_view(), name="post_delete"),
]

# blog extras
urlpatterns += [
    path("rss/", feeds.RSSBlogFeed(), name="rss_feed"),
    path("notifications/", views.Notification.as_view(), name="notification"),
    path(
        "notifications/unsubscribe/",
        views.NotificationUnsubscribe.as_view(),
        name="notification_unsubscribe",
    ),
    path(
        "notifications/unsubscribe/<uuid:unsubscribe_key>/",
        views.notification_unsubscribe_key,
        name="notification_unsubscribe_key",
    ),
]

# comments
urlpatterns += [
    path(
        "blog/<slug:slug>/comments/create/",
        views.CommentCreate.as_view(),
        name="comment_create",
    ),
    path(
        "blog/<slug:slug>/comments/<int:pk>/delete/",
        views.CommentDelete.as_view(),
        name="comment_delete",
    ),
]

# blog settings
urlpatterns += [
    path("webring/", views.WebringUpdate.as_view(), name="blog_webring"),
    path("import/", views.BlogImport.as_view(), name="blog_import"),
    path("export/", views_export.blog_export, name="blog_export"),
    path(
        "export/markdown/",
        views_export.blog_export_markdown,
        name="blog_export_markdown",
    ),
    path("export/zola/", views_export.blog_export_zola, name="blog_export_zola"),
    path("export/hugo/", views_export.blog_export_hugo, name="blog_export_hugo"),
]

# images
urlpatterns += [
    path("images/<slug:slug>.<slug:extension>", views.image_raw, name="image_raw"),
    re_path(
        r"^images/(?P<options>\?[\w\=]+)?$",  # e.g. images/ or images/?raw=true
        views.ImageList.as_view(),
        name="image_list",
    ),
    path("images/<slug:slug>/", views.ImageDetail.as_view(), name="image_detail"),
    path("images/<slug:slug>/edit/", views.ImageUpdate.as_view(), name="image_update"),
    path(
        "images/<slug:slug>/delete/", views.ImageDelete.as_view(), name="image_delete",
    ),
]

# analytics
urlpatterns += [
    path("analytics/", views.AnalyticList.as_view(), name="analytic_list"),
    path(
        "analytics/<slug:post_slug>/",
        views.AnalyticDetail.as_view(),
        name="analytic_detail",
    ),
]

# pages - needs to be last due to <slug>
urlpatterns += [
    path("pages/", views.PageList.as_view(), name="page_list"),
    path("pages/create/", views.PageCreate.as_view(), name="page_create"),
    path("<slug:slug>/", views.PageDetail.as_view(), name="page_detail"),
    path("<slug:slug>/edit/", views.PageUpdate.as_view(), name="page_update"),
    path("<slug:slug>/delete/", views.PageDelete.as_view(), name="page_delete"),
]
