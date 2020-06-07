from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from main import forms, helpers, models


@login_required
def blog_index(request):
    return redirect(
        f'//{request.user.username}.{settings.CANONICAL_HOST}{reverse("index")}'
    )


@login_required
def dashboard(request):
    if hasattr(request, "subdomain"):
        return redirect("//" + settings.CANONICAL_HOST + reverse("dashboard"))

    return render(request, "main/dashboard.html")


def index(request):
    if hasattr(request, "subdomain"):
        if request.subdomain == "random":
            random_user = models.User.objects.all().order_by("?")[0]
            return redirect(
                f'//{random_user.username}.{settings.CANONICAL_HOST}{reverse("index")}'
            )

        if models.User.objects.filter(username=request.subdomain).exists():
            user = models.User.objects.get(username=request.subdomain)
            return render(
                request,
                "main/blog_index.html",
                {
                    "user": user,
                    "posts": models.Post.objects.filter(owner=user).order_by(
                        "-created_at"
                    ),
                    "subdomain": request.subdomain,
                },
            )
        else:
            return redirect("//" + settings.CANONICAL_HOST + reverse("index"))

    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "main/landing.html")


class Logout(DjLogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.add_message(request, messages.INFO, "logged out")
        return super().dispatch(request, *args, **kwargs)


class UserDetail(LoginRequiredMixin, DetailView):
    model = models.User

    def dispatch(self, request, *args, **kwargs):
        if request.user.id != kwargs["pk"]:
            raise PermissionDenied()

        if hasattr(request, "subdomain"):
            return redirect(
                "//"
                + settings.CANONICAL_HOST
                + reverse("user_detail", args=(request.user.id,))
            )

        return super().dispatch(request, *args, **kwargs)


class UserCreate(SuccessMessageMixin, CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "main/user_create.html"
    success_message = "welcome! login with your new credentials"

    def form_valid(self, form):
        if helpers.is_disallowed(form.cleaned_data.get("username")):
            form.add_error("username", "This username is not available.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)


class UserUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.User
    fields = [
        "username",
        "email",
        "blog_title",
        "blog_byline",
        "custom_domain",
        "about",
    ]
    template_name = "main/user_update.html"
    success_message = "settings updated"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.id != kwargs["pk"]:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.cleaned_data.get("custom_domain"):
            return super().form_valid(form)

        if models.User.objects.filter(
            custom_domain=form.cleaned_data.get("custom_domain")
        ).exists():
            form.add_error(
                "custom_domain",
                "This domain name is already connected to a mataroa blog.",
            )
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)


class UserDelete(LoginRequiredMixin, DeleteView):
    model = models.User
    success_url = reverse_lazy("index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.id != kwargs["pk"]:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class PostDetail(DetailView):
    model = models.Post

    def get_queryset(self):
        queryset = models.Post.objects.filter(owner__username=self.request.subdomain)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data(**kwargs)
        if hasattr(self.request, "subdomain"):
            context["blog_title"] = models.User.objects.get(
                username=self.request.subdomain
            ).blog_title
        return context

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "subdomain"):
            if request.user.is_authenticated:
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                return redirect("index")

        return super().dispatch(request, *args, **kwargs)


class PostCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Post
    fields = ["title", "body"]
    success_message = "'%(title)s' was created"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.slug = helpers.get_post_slug(self.object.title, self.request.user)
        self.object.owner = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "subdomain") and request.method == "GET":
            return redirect("//" + settings.CANONICAL_HOST + reverse("post_create"))
        else:
            return super().dispatch(request, *args, **kwargs)


class PostUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Post
    fields = ["title", "body", "slug"]
    success_message = "post updated"

    def get_queryset(self):
        queryset = models.Post.objects.filter(
            owner__username=self.request.user.username
        )
        return queryset

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "subdomain"):
            if request.user.is_authenticated:
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                return redirect("index")

        if request.user.username != request.subdomain:
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


class PostDelete(LoginRequiredMixin, DeleteView):
    model = models.Post
    success_url = reverse_lazy("index")

    def get_queryset(self):
        queryset = models.Post.objects.filter(
            owner__username=self.request.user.username
        )
        return queryset

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "subdomain"):
            if request.user.is_authenticated:
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                return redirect("index")

        if request.user.username != request.subdomain:
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


def ethics(request):
    return render(request, "main/ethics.html")


class InterestView(SuccessMessageMixin, FormView):
    form_class = forms.InterestForm
    template_name = "main/interest.html"
    success_url = reverse_lazy("index")
    success_message = "thank you for your interest! we'll be in touch :)"

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)


def markdown_guide(request):
    return render(request, "main/markdown_guide.html")


def acme_challenge(request):
    return render(request, "main/acme_challenge.txt")
