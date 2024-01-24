from django.contrib import admin
from django.urls import include, path, re_path

from main import feeds
from main.views import adminextra, api, billing, export, general

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
    path(
        "accounts/create/",
        general.UserCreateStepOne.as_view(),
        name="user_create",
    ),
    path(
        "accounts/humanity-diagnostics/<uuid:onboard_code>/",
        general.UserCreateStepTwo.as_view(),
        name="user_create_step_two",
    ),
    path("accounts/edit/", general.UserUpdate.as_view(), name="user_update"),
    path("accounts/delete/", general.UserDelete.as_view(), name="user_delete"),
    path("accounts/domain/", general.domain_check, name="domain_check"),
]

# adminextra
urlpatterns += [
    path("adminextra/cards/", adminextra.user_cards, name="adminextra_user_cards"),
    path("adminextra/users/", adminextra.user_list, name="adminextra_user_list"),
    path(
        "adminextra/users/<int:user_id>/approve/",
        adminextra.user_approve,
        name="adminextra_user_approve",
    ),
    path(
        "adminextra/users/<int:user_id>/unapprove/",
        adminextra.user_unapprove,
        name="adminextra_user_unapprove",
    ),
    path(
        "adminextra/users/<int:user_id>/delete/",
        adminextra.user_delete,
        name="adminextra_user_delete",
    ),
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
        "billing/subscribe/",
        billing.BillingSubscribe.as_view(),
        name="billing_subscribe",
    ),
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
        "billing/subscription/welcome/",
        billing.billing_welcome,
        name="billing_welcome",
    ),
    path(
        "billing/subscription/card/confirm/",
        billing.billing_card_confirm,
        name="billing_card_confirm",
    ),
    path(
        "billing/subscription/cancel/",
        billing.BillingCancel.as_view(),
        name="billing_subscription_cancel",
    ),
    path(
        "billing/stripe/webhook/",
        billing.billing_stripe_webhook,
        name="billing_stripe_webhook",
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
