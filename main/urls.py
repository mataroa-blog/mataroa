from django.contrib import admin
from django.urls import include, path

from main import views

admin.site.site_header = "mataroa administration"

# indexes
urlpatterns = [
    path("", views.index, name="index"),
    path("root/", views.root_index, name="root_index"),
    path("blog/<slug:username>", views.blog_index, name="blog_index"),
]

# user system
urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", views.UserCreate.as_view(), name="user_create"),
    path("accounts/<int:pk>/", views.UserDetail.as_view(), name="user_detail"),
    path("accounts/<int:pk>/edit/", views.UserUpdate.as_view(), name="user_update"),
    path("accounts/<int:pk>/delete/", views.UserDelete.as_view(), name="user_delete"),
]
