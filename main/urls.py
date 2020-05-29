from django.contrib import admin
from django.urls import include, path

from main import views

admin.site.site_header = "mataroa administration"

# indexes
urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard", views.dashboard, name="dashboard"),
]

# user system — available for //mataroa.blog
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", views.UserCreate.as_view(), name="user_create"),
    path("accounts/<int:pk>/", views.UserDetail.as_view(), name="user_detail"),
    path("accounts/<int:pk>/edit/", views.UserUpdate.as_view(), name="user_update"),
    path("accounts/<int:pk>/delete/", views.UserDelete.as_view(), name="user_delete"),
]

# posts crud — available for //myblog.mataroa.blog
urlpatterns += [
    path("blog/create/", views.PostCreate.as_view(), name="post_create"),
    path("blog/<int:pk>/", views.PostDetail.as_view(), name="post_detail"),
    path("blog/<int:pk>/edit/", views.PostUpdate.as_view(), name="post_update",),
    path("blog/<int:pk>/delete/", views.PostDelete.as_view(), name="post_delete",),
    path("export/", views.blog_export, name="blog_export"),
]
