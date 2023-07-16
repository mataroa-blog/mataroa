from django.contrib import admin
from django.urls import include, path, re_path

from main import feeds
from main.views import api, billing, export, general

admin.site.site_header = "mataroa admin"

# general
urlpatterns = [
    path("", general.index, name="index"),
    path("blog/", general.blog_index, name="blog_index"),
    path("dashboard/", general.dashboard, name="dashboard"),
    path("modus/operandi/", general.operandi, name="operandi"),
    path("modus/transparency/", general.transparency, name="transparency"),
    path("modus/privacy/", general.privacy_redir, name="privacy_redir"),
    path("guides/markdown/", general.guides_markdown, name="guides_markdown"),
    path("guides/images/", general.guides_images, name="guides_images"),
    path("guides/comments/", general.guides_comments, name="guides_comments"),
    path("guides/comparisons/", general.comparisons, name="comparisons"),
]

# user system
urlpatterns += [
    path("accounts/logout/", general.Logout.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", general.user_create_disabled, name="user_create"),
    path(
        "accounts/create/consciousness-only/",
        general.UserCreate.as_view(),
        name="user_create_invite",
    ),
    path("accounts/edit/", general.UserUpdate.as_view(), name="user_update"),
    path("accounts/delete/", general.UserDelete.as_view(), name="user_delete"),
]

# moderation pages
urlpatterns += [
    path("mod/users/premium/", general.mod_users_premium, name="mod_users_premium"),
    path("mod/users/new/", general.mod_users_new, name="mod_users_new"),
    path(
        "mod/users/new-with-posts/",
        general.mod_users_new_with_posts,
        name="mod_users_new_with_posts",
    ),
    path(
        "mod/users/grandfather/",
        general.mod_users_grandfather,
        name="mod_users_grandfather",
    ),
    path("mod/users/staff/", general.mod_users_staff, name="mod_users_staff"),
    path("mod/users/active/", general.mod_users_active, name="mod_users_active"),
    path(
        "mod/users/active-with-posts/",
        general.mod_users_active_with_posts,
        name="mod_users_active_with_posts",
    ),
    path(
        "mod/users/active-nonnew/",
        general.mod_users_active_nonnew,
        name="mod_users_active_nonnew",
    ),
    path(
        "mod/users/active-nonnew-with-posts/",
        general.mod_users_active_nonnew_with_posts,
        name="mod_users_active_nonnew_with_posts",
    ),
    path(
        "mod/users/random-with-posts/",
        general.mod_users_random_with_posts,
        name="mod_users_random_with_posts",
    ),
    path("mod/users/<int:user_id>/expel/", general.mod_expel, name="mod_expel"),
    path("mod/posts/new/", general.mod_posts_new, name="mod_posts_new"),
    path("mod/posts/recently/", general.mod_posts_recently, name="mod_posts_recently"),
    path("mod/pages/new/", general.mod_pages_new, name="mod_pages_new"),
    path("mod/pages/recently/", general.mod_pages_recently, name="mod_pages_recently"),
    path("mod/comments/", general.mod_comments, name="mod_comments"),
]

# blog posts and post snapshots
urlpatterns += [
    path(
        "post-backups/create/", general.SnapshotCreate.as_view(), name="snapshot_create"
    ),
    path("post-backups/", general.SnapshotList.as_view(), name="snapshot_list"),
    path(
        "post-backups/<int:pk>/",
        general.SnapshotDetail.as_view(),
        name="snapshot_detail",
    ),
    path("new/post/", general.PostCreate.as_view(), name="post_create"),
    path("blog/<slug:slug>/", general.PostDetail.as_view(), name="post_detail"),
    path("posts/<slug:slug>/", general.post_detail_redir, name="post_detail_redir_a"),
    path("post/<slug:slug>/", general.post_detail_redir, name="post_detail_redir_b"),
    path("blog/<slug:slug>/edit/", general.PostUpdate.as_view(), name="post_update"),
    path("blog/<slug:slug>/delete/", general.PostDelete.as_view(), name="post_delete"),
]

# blog extras
urlpatterns += [
    path("rss/", feeds.RSSBlogFeed(), name="rss_feed"),
    path("sitemap.xml", general.sitemap, name="sitemap"),
    path("newsletter/", general.Notification.as_view(), name="notification_subscribe"),
    path(
        "newsletter/unsubscribe/",
        general.NotificationUnsubscribe.as_view(),
        name="notification_unsubscribe",
    ),
    path(
        "newsletter/unsubscribe/<uuid:unsubscribe_key>/",
        general.notification_unsubscribe_key,
        name="notification_unsubscribe_key",
    ),
    path(
        "notifications/",
        general.NotificationRecordList.as_view(),
        name="notificationrecord_list",
    ),
    path(
        "notifications/<int:pk>/delete/",
        general.NotificationRecordDelete.as_view(),
        name="notificationrecord_delete",
    ),
    path(
        "notifications/subscribers",
        general.NotificationList.as_view(),
        name="notification_list",
    ),
]

# comments
urlpatterns += [
    path("comments/pending/", general.CommentPending.as_view(), name="comment_pending"),
    path(
        "blog/<slug:slug>/comments/create/author/",
        general.CommentCreateAuthor.as_view(),
        name="comment_create_author",
    ),
    path(
        "blog/<slug:slug>/comments/create/",
        general.CommentCreate.as_view(),
        name="comment_create",
    ),
    path(
        "blog/<slug:slug>/comments/<int:pk>/delete/",
        general.CommentDelete.as_view(),
        name="comment_delete",
    ),
    path(
        "blog/<slug:slug>/comments/<int:pk>/approve/",
        general.CommentApprove.as_view(),
        name="comment_approve",
    ),
]

# billing
urlpatterns += [
    path("billing/", billing.billing_index, name="billing_index"),
    path("billing/card/", billing.BillingCard.as_view(), name="billing_card"),
    path(
        "billing/card/<slug:stripe_payment_method_id>/delete/",
        billing.BillingCardDelete.as_view(),
        name="billing_card_delete",
    ),
    path(
        "billing/card/<slug:stripe_payment_method_id>/default/",
        billing.billing_card_default,
        name="billing_card_default",
    ),
    path(
        "billing/subscription/",
        billing.billing_subscription,
        name="billing_subscription",
    ),
    path(
        "billing/subscription/cancel/",
        billing.BillingCancel.as_view(),
        name="billing_subscription_cancel",
    ),
]

# blog import, export, webring
urlpatterns += [
    path("webring/", general.WebringUpdate.as_view(), name="webring"),
    path("import/", general.BlogImport.as_view(), name="blog_import"),
    path("export/", export.export_index, name="export_index"),
    path(
        "export/markdown/",
        export.export_markdown,
        name="export_markdown",
    ),
    path("export/zola/", export.export_zola, name="export_zola"),
    path("export/hugo/", export.export_hugo, name="export_hugo"),
    path("export/epub/", export.export_epub, name="export_epub"),
    path("export/print/", export.export_print, name="export_print"),
    path(
        "export/unsubscribe/<uuid:unsubscribe_key>/",
        export.export_unsubscribe_key,
        name="export_unsubscribe_key",
    ),
]

# images
urlpatterns += [
    path("images/<slug:slug>.<slug:extension>", general.image_raw, name="image_raw"),
    re_path(
        r"^images/(?P<options>\?[\w\=]+)?$",  # e.g. images/ or images/?raw=true
        general.ImageList.as_view(),
        name="image_list",
    ),
    path("images/<slug:slug>/", general.ImageDetail.as_view(), name="image_detail"),
    path(
        "images/<slug:slug>/edit/", general.ImageUpdate.as_view(), name="image_update"
    ),
    path(
        "images/<slug:slug>/delete/",
        general.ImageDelete.as_view(),
        name="image_delete",
    ),
]

# analytics
urlpatterns += [
    path("analytics/", general.AnalyticList.as_view(), name="analytic_list"),
    path(
        "analytics/post/<slug:post_slug>/",
        general.AnalyticPostDetail.as_view(),
        name="analytic_post_detail",
    ),
    path(
        "analytics/page/<slug:page_path>/",
        general.AnalyticPageDetail.as_view(),
        name="analytic_page_detail",
    ),
]

# api
urlpatterns += [
    path("api/docs/", api.api_docs, name="api_docs"),
    path("api/reset/", api.APIKeyReset.as_view(), name="api_reset"),
    path("api/posts/", api.api_posts, name="api_posts"),
    path("api/posts/<slug:slug>/", api.api_post, name="api_post"),
]

# pages - needs to be last due to <slug>
urlpatterns += [
    path("pages/", general.PageList.as_view(), name="page_list"),
    path("new/page/", general.PageCreate.as_view(), name="page_create"),
    path("<slug:slug>/", general.PageDetail.as_view(), name="page_detail"),
    path("<slug:slug>/edit/", general.PageUpdate.as_view(), name="page_update"),
    path("<slug:slug>/delete/", general.PageDelete.as_view(), name="page_delete"),
]
