from django.contrib import admin
from django.urls import include, path

from main import views

admin.site.site_header = "mataroa administration"

urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create/", views.UserCreate.as_view(), name="user_create"),
    path("accounts/<int:pk>/", views.UserDetail.as_view(), name="user_detail"),
    path("accounts/<int:pk>/edit/", views.UserUpdate.as_view(), name="user_update"),
    path("accounts/<int:pk>/delete/", views.UserDelete.as_view(), name="user_delete"),
]
