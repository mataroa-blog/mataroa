from django.contrib import admin
from django.urls import include, path, re_path

from main import feeds, views, views_api, views_billing, views_export

admin.site.site_header = "mataroa admin"

# general
urlpatterns = [
    path("", views.index, name="index"),
    path("blog/", views.blog_index, name="blog_index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("modus/operandi/", views.modus, name="modus"),
    path("modus/privacy/", views.privacy, name="privacy"),
    path("modus/transparency/", views.transparency, name="transparency"),
    path("guides/markdown/", views.guides_markdown, name="guides_markdown"),
    path("guides/images/", views.guides_images, name="guides_images"),
    path("guides/comments/", views.guides_comments, name="guides_comments"),
    path("guides/comparisons/", views.comparisons, name="comparisons"),
]

# user system
urlpatterns += [
    path("accounts/logout/", views.Logout.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", views.UserCreate.as_view(), name="user_create"),
    path("accounts/edit/", views.UserUpdate.as_view(), name="user_update"),
    path("accounts/delete/", views.UserDelete.as_view(), name="user_delete"),
]

# atua pages
urlpatterns += [
    path("atua/users/premium/", views.atua_users_premium, name="atua_users_premium"),
    path("atua/users/new/", views.atua_users_new, name="atua_users_new"),
    path(
        "atua/users/grandfather/",
        views.atua_users_grandfather,
        name="atua_users_grandfather",
    ),
    path("atua/users/staff/", views.atua_users_staff, name="atua_users_staff"),
    path("atua/users/active/", views.atua_users_active, name="atua_users_active"),
    path(
        "atua/users/active-nonnew/",
        views.atua_users_active_nonnew,
        name="atua_users_active_nonnew",
    ),
    path("atua/posts/new/", views.atua_posts_new, name="atua_posts_new"),
    path("atua/posts/recently/", views.atua_posts_recently, name="atua_posts_recently"),
    path("atua/pages/new/", views.atua_pages_new, name="atua_pages_new"),
    path("atua/pages/recently/", views.atua_pages_recently, name="atua_pages_recently"),
    path("atua/comments/", views.atua_comments, name="atua_comments"),
]

# blog posts and post snapshots
urlpatterns += [
    path("snapshots/create/", views.SnapshotCreate.as_view(), name="snapshot_create"),
    path("snapshots/", views.SnapshotList.as_view(), name="snapshot_list"),
    path("snapshots/<int:pk>/", views.SnapshotDetail.as_view(), name="snapshot_detail"),
    path("new/post/", views.PostCreate.as_view(), name="post_create"),
    path("blog/<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),
    path("posts/<slug:slug>/", views.post_detail_redir, name="post_detail_redir_a"),
    path("post/<slug:slug>/", views.post_detail_redir, name="post_detail_redir_b"),
    path("blog/<slug:slug>/edit/", views.PostUpdate.as_view(), name="post_update"),
    path("blog/<slug:slug>/delete/", views.PostDelete.as_view(), name="post_delete"),
]

# blog extras
urlpatterns += [
    path("rss/", feeds.RSSBlogFeed(), name="rss_feed"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("newsletter/", views.Notification.as_view(), name="notification_subscribe"),
    path(
        "newsletter/unsubscribe/",
        views.NotificationUnsubscribe.as_view(),
        name="notification_unsubscribe",
    ),
    path(
        "newsletter/unsubscribe/<uuid:unsubscribe_key>/",
        views.notification_unsubscribe_key,
        name="notification_unsubscribe_key",
    ),
    path(
        "notifications/",
        views.NotificationRecordList.as_view(),
        name="notificationrecord_list",
    ),
    path(
        "notifications/<int:pk>/delete/",
        views.NotificationRecordDelete.as_view(),
        name="notificationrecord_delete",
    ),
    path(
        "notifications/subscribers",
        views.NotificationList.as_view(),
        name="notification_list",
    ),
]

# comments
urlpatterns += [
    path("comments/pending/", views.CommentPending.as_view(), name="comment_pending"),
    path(
        "blog/<slug:slug>/comments/create/author/",
        views.CommentCreateAuthor.as_view(),
        name="comment_create_author",
    ),
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
    path(
        "blog/<slug:slug>/comments/<int:pk>/approve/",
        views.CommentApprove.as_view(),
        name="comment_approve",
    ),
]

# billing
urlpatterns += [
    path("billing/", views_billing.billing_index, name="billing_index"),
    path("billing/card/", views_billing.BillingCard.as_view(), name="billing_card"),
    path(
        "billing/card/<slug:stripe_payment_method_id>/delete/",
        views_billing.BillingCardDelete.as_view(),
        name="billing_card_delete",
    ),
    path(
        "billing/card/<slug:stripe_payment_method_id>/default/",
        views_billing.billing_card_default,
        name="billing_card_default",
    ),
    path(
        "billing/subscription/",
        views_billing.billing_subscription,
        name="billing_subscription",
    ),
    path(
        "billing/subscription/cancel/",
        views_billing.BillingCancel.as_view(),
        name="billing_subscription_cancel",
    ),
]

# blog import, export, webring
urlpatterns += [
    path("webring/", views.WebringUpdate.as_view(), name="blog_webring"),
    path("import/", views.BlogImport.as_view(), name="blog_import"),
    path("export/", views_export.export_index, name="export_index"),
    path(
        "export/markdown/",
        views_export.export_markdown,
        name="export_markdown",
    ),
    path("export/zola/", views_export.export_zola, name="export_zola"),
    path("export/hugo/", views_export.export_hugo, name="export_hugo"),
    path("export/epub/", views_export.export_epub, name="export_epub"),
    path("export/print/", views_export.export_print, name="export_print"),
    path(
        "export/unsubscribe/<uuid:unsubscribe_key>/",
        views_export.export_unsubscribe_key,
        name="export_unsubscribe_key",
    ),
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
        "images/<slug:slug>/delete/",
        views.ImageDelete.as_view(),
        name="image_delete",
    ),
]

# analytics
urlpatterns += [
    path("analytics/", views.AnalyticList.as_view(), name="analytic_list"),
    path(
        "analytics/post/<slug:post_slug>/",
        views.AnalyticPostDetail.as_view(),
        name="analytic_post_detail",
    ),
    path(
        "analytics/page/<slug:page_path>/",
        views.AnalyticPageDetail.as_view(),
        name="analytic_page_detail",
    ),
]

# api
urlpatterns += [
    path("api/docs/", views_api.api_docs, name="api_docs"),
    path("api/reset/", views_api.APIKeyReset.as_view(), name="api_reset"),
    path("api/posts/", views_api.api_posts, name="api_posts"),
    path("api/posts/<slug:slug>/", views_api.api_post, name="api_post"),
]

# pages - needs to be last due to <slug>
urlpatterns += [
    path("pages/", views.PageList.as_view(), name="page_list"),
    path("new/page/", views.PageCreate.as_view(), name="page_create"),
    path("<slug:slug>/", views.PageDetail.as_view(), name="page_detail"),
    path("<slug:slug>/edit/", views.PageUpdate.as_view(), name="page_update"),
    path("<slug:slug>/delete/", views.PageDelete.as_view(), name="page_delete"),
]
