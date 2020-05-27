from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from main import forms, models


def index(request):
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
