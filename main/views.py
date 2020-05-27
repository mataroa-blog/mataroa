from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from main import forms, models


def root_index(request):
    if request.META["HTTP_HOST"] != settings.CANONICAL_HOST:
        return redirect(settings.CANONICAL_HOST)


def blog_index(request, username):
    return redirect("//" + username + "." + settings.CANONICAL_HOST[2:])


def index(request):
    if "HTTP_HOST" not in request.META:
        return render(request, "main/index.html")

    host = request.META["HTTP_HOST"]
    if host == settings.CANONICAL_HOST:
        return render(request, "main/index.html")
    elif ".mataroa.blog" in host:
        subdomain = host.split(".")[0]
        if models.User.objects.filter(username=subdomain).exists():
            user = models.User.objects.get(username=subdomain)
            return render(
                request,
                "main/blog_index.html",
                {"user": user, "posts": models.Post.objects.filter(owner=user)},
            )

    return render(request, "main/index.html")


class UserDetail(DetailView):
    model = models.User


class UserCreate(SuccessMessageMixin, CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "main/user_create.html"
    success_message = "Welcome!"


class UserUpdate(SuccessMessageMixin, UpdateView):
    model = models.User
    fields = ["username", "email"]
    success_message = "%(username)s updated successfully"
    template_name = "main/user_update.html"


class UserDelete(DeleteView):
    model = models.User
    success_url = reverse_lazy("index")
