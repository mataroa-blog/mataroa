import io
import uuid
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from main import forms, models


@login_required
def dashboard(request):
    if "HTTP_HOST" in request.META and (
        request.META["HTTP_HOST"] != settings.CANONICAL_HOST
    ):
        return redirect("//" + settings.CANONICAL_HOST + reverse("dashboard"))

    return render(request, "main/dashboard.html")


def index(request):
    if "HTTP_HOST" not in request.META:
        return render(request, "main/index.html")

    host = request.META["HTTP_HOST"]
    if host == settings.CANONICAL_HOST:
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "main/index.html")
    elif f".{settings.CANONICAL_HOST}" in host:
        subdomain = host.split(".")[0]
        if models.User.objects.filter(username=subdomain).exists():
            user = models.User.objects.get(username=subdomain)
            return render(
                request,
                "main/blog_index.html",
                {
                    "user": user,
                    "posts": models.Post.objects.filter(owner=user),
                    "subdomain": subdomain,
                },
            )

    return render(request, "main/index.html")


class UserDetail(LoginRequiredMixin, DetailView):
    model = models.User

    def dispatch(self, request, *args, **kwargs):
        if "HTTP_HOST" in request.META and (
            request.META["HTTP_HOST"] != settings.CANONICAL_HOST
        ):
            return redirect(
                "//"
                + settings.CANONICAL_HOST
                + reverse("user_detail", args=(request.user.id,))
            )
        else:
            return super().dispatch(request, *args, **kwargs)


class UserCreate(SuccessMessageMixin, CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "main/user_create.html"
    success_message = "Welcome!"


class UserUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.User
    fields = ["username", "email"]
    success_message = "%(username)s updated successfully"
    template_name = "main/user_update.html"


class UserDelete(LoginRequiredMixin, DeleteView):
    model = models.User
    success_url = reverse_lazy("index")


class PostDetail(DetailView):
    model = models.Post

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data(**kwargs)
        if "HTTP_HOST" in self.request.META:
            host = self.request.META["HTTP_HOST"]
            subdomain = host.split(".")[0]
            context["subdomain"] = subdomain
            context["blog_title"] = models.User.objects.get(
                username=subdomain
            ).blog_title
        return context

    def dispatch(self, request, *args, **kwargs):
        if "HTTP_HOST" in request.META and (
            request.META["HTTP_HOST"] == settings.CANONICAL_HOST
        ):
            if request.user.is_authenticated:
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                return redirect("dashboard")
        else:
            return super().dispatch(request, *args, **kwargs)


class PostCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Post
    fields = ["title", "body"]
    success_message = "%(title)s was created successfully"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        if "HTTP_HOST" in request.META and (
            request.META["HTTP_HOST"] != settings.CANONICAL_HOST
        ):
            return redirect("//" + settings.CANONICAL_HOST + reverse("post_create"))
        else:
            return super().dispatch(request, *args, **kwargs)


class PostUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Post
    fields = ["title", "body"]
    success_message = "%(title)s updated successfully"


class PostDelete(LoginRequiredMixin, DeleteView):
    model = models.Post
    success_url = reverse_lazy("index")


@login_required
def blog_export(request):
    # load zola templates
    with open("./zola_export_base/config.toml", "r") as zola_config_file:
        zola_config = (
            zola_config_file.read()
            .replace("example.com", f"{request.user.username}.mataroa.blog")
            .replace("Example blog title", f"{request.user.username} blog")
        )
    with open("./zola_export_base/style.css", "r") as zola_styles_file:
        zola_styles = zola_styles_file.read()
    with open("./zola_export_base/template_index.html", "r") as zola_index_file:
        zola_index = zola_index_file.read()
    with open("./zola_export_base/config.toml", "r") as zola_post_file:
        zola_post = zola_post_file.read()

    # get all posts and add them into export_posts encoded
    posts = models.Post.objects.all()
    export_posts = []
    for p in posts:
        title = p.title.replace(":", "-") + ".md"
        export_posts.append((title, io.BytesIO(p.body.encode())))

    # create zip archive in memory
    export_name = "export-" + str(uuid.uuid4())[:8]
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer, "a", zipfile.ZIP_DEFLATED, False
    ) as export_archive:
        export_archive.writestr(export_name + "/config.toml", zola_config)
        export_archive.writestr(export_name + "/static/style.css", zola_styles)
        export_archive.writestr(export_name + "/templates/index.html", zola_index)
        export_archive.writestr(export_name + "/templates/post.html", zola_post)
        for file_name, data in export_posts:
            export_archive.writestr(
                export_name + "/content/" + file_name, data.getvalue()
            )

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f"attachment; filename={export_name}.zip"
    return response


def ethics(request):
    return render(request, "main/ethics.html")
