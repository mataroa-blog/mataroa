import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sitemaps.views import sitemap as DjSitemapView
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView

from main import denylist, forms, models, util
from main.sitemaps import PageSitemap, PostSitemap, StaticSitemap


@login_required
def blog_index(request):
    return redirect(
        f'//{request.user.username}.{settings.CANONICAL_HOST}{reverse("index")}'
    )


@login_required
def dashboard(request):
    if hasattr(request, "subdomain"):
        return redirect("//" + settings.CANONICAL_HOST + reverse("dashboard"))

    return render(
        request,
        "main/dashboard.html",
        {
            "billing_enabled": bool(settings.STRIPE_API_KEY),
        },
    )


def index(request):
    if hasattr(request, "subdomain"):
        if models.User.objects.filter(username=request.subdomain).exists():
            if request.user.is_authenticated and request.user == request.blog_user:
                posts = models.Post.objects.filter(owner=request.blog_user).defer(
                    "body"
                )
            else:
                models.AnalyticPage.objects.create(user=request.blog_user, path="index")
                posts = (
                    models.Post.objects.filter(
                        owner=request.blog_user,
                        published_at__isnull=False,
                        published_at__lte=timezone.now().date(),
                    )
                    .defer("body")
                    .order_by("-published_at")
                )

            return render(
                request,
                "main/blog_index.html",
                {
                    "subdomain": request.subdomain,
                    "blog_user": request.blog_user,
                    "posts": posts,
                    "pages": models.Page.objects.filter(
                        owner=request.blog_user, is_hidden=False
                    ).defer("body"),
                },
            )
        else:
            return redirect("//" + settings.CANONICAL_HOST + reverse("index"))

    if request.user.is_authenticated:
        return redirect("blog_index")

    return render(request, "main/landing.html")


class Logout(DjLogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.add_message(request, messages.INFO, "logged out")
        return super().dispatch(request, *args, **kwargs)


class UserCreate(CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy("dashboard")
    template_name = "main/user_create.html"
    success_message = "welcome to mataroa :)"

    def form_valid(self, form):
        if util.is_disallowed(form.cleaned_data.get("username")):
            form.add_error("username", "This username is not available.")
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save(commit=False)
        self.object.blog_title = self.object.username
        self.object.save()
        user = authenticate(
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password1"),
        )
        login(self.request, user)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


class UserUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.User
    fields = [
        "username",
        "email",
        "blog_title",
        "blog_byline",
        "footer_note",
        "theme_zialucia",
        "custom_domain",
        "comments_on",
        "notifications_on",
        "mail_export_on",
        "about",
        "redirect_domain",
    ]
    template_name = "main/user_update.html"
    success_message = "settings updated"
    success_url = reverse_lazy("dashboard")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        # we need to check if more than one users have the same custom domain
        if not form.cleaned_data.get("custom_domain"):
            # if it's not submitted, then just return
            return super().form_valid(form)

        if (
            models.User.objects.filter(
                custom_domain=form.cleaned_data.get("custom_domain")
            )
            .exclude(id=self.request.user.id)  # exclude current user
            .exists()
        ):
            form.add_error(
                "custom_domain",
                "This domain name is already connected to a mataroa blog.",
            )
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_valid(form)


class UserDelete(LoginRequiredMixin, DeleteView):
    model = models.User
    success_url = reverse_lazy("index")

    def get_object(self):
        return self.request.user


def post_detail_redir(request, slug):
    return redirect("post_detail", slug=slug, permanent=True)


class PostDetail(DetailView):
    model = models.Post

    def get_queryset(self):
        queryset = models.Post.objects.filter(owner__username=self.request.subdomain)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request, "subdomain"):
            context["blog_user"] = self.request.blog_user
            context["pages"] = models.Page.objects.filter(
                owner__username=self.request.subdomain, is_hidden=False
            )
            context["comments"] = models.Comment.objects.filter(
                post=self.object, is_approved=True
            )

        # do not record analytic if post is authed user's
        if (
            self.request.user.is_authenticated
            and self.request.user == self.object.owner
        ):
            return context
        models.AnalyticPost.objects.create(post=self.object)

        return context

    def dispatch(self, request, *args, **kwargs):
        # if there is no subdomain on this request
        if not hasattr(request, "subdomain"):
            if request.user.is_authenticated:
                # if post is requested without subdomain and authed
                # then redirect them to the subdomain'ed post
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                # if post is requested without subdomain and non-authed
                # then redirect to index
                return redirect("index")

        return super().dispatch(request, *args, **kwargs)


class PostCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Post
    fields = ["title", "published_at", "body"]
    success_message = "'%(title)s' was created"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.slug = util.get_post_slug(self.object.title, self.request.user)
        self.object.owner = self.request.user
        self.object.body = util.remove_control_chars(self.object.body)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "subdomain") and request.method == "GET":
            return redirect("//" + settings.CANONICAL_HOST + reverse("post_create"))
        else:
            return super().dispatch(request, *args, **kwargs)


class PostUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Post
    fields = ["title", "slug", "published_at", "body"]
    success_message = "post updated"

    def get_queryset(self):
        queryset = models.Post.objects.filter(
            owner__username=self.request.user.username
        )
        return queryset

    def form_valid(self, form):
        # hidden code for slug: if slug is ":gen" then generate it from the title
        if form.cleaned_data.get("slug") == ":gen":
            self.object = form.save(commit=False)
            self.object.slug = util.get_post_slug(
                self.object.title, self.request.user, post=self.object
            )
            self.object.body = util.remove_control_chars(self.object.body)
            self.object.save()
            return super().form_valid(form)

        # normalise and validate slug
        self.object = form.save(commit=False)
        updated_slug = form.cleaned_data.get("slug")
        self.object.slug = util.get_post_slug(
            updated_slug, self.request.user, post=self.object
        )
        self.object.save()

        return super().form_valid(form)

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
    success_message = "post '%(title)s' deleted"

    def get_queryset(self):
        queryset = models.Post.objects.filter(
            owner__username=self.request.user.username
        )
        return queryset

    def form_view(self, request):
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, self.success_message % self.object.__dict__)
        return HttpResponseRedirect(success_url)

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


class CommentCreate(SuccessMessageMixin, CreateView):
    model = models.Comment
    fields = ["name", "email", "body"]
    success_message = "your comment is pending review"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post"] = models.Post.objects.get(
            owner__username=self.request.subdomain, slug=self.kwargs["slug"]
        )
        return context

    def form_valid(self, form):
        # prevent comment creation on comments_on=False blogs
        if not models.User.objects.get(username=self.request.subdomain).comments_on:
            form.add_error(None, "No comments allowed on this blog.")
            return self.render_to_response(self.get_context_data(form=form))

        self.object = form.save(commit=False)
        if settings.COMMENTS_MODERATION:
            self.object.is_approved = False
        self.object.post = models.Post.objects.get(
            owner__username=self.request.subdomain, slug=self.kwargs["slug"]
        )
        self.object.save()
        messages.add_message(self.request, messages.INFO, self.success_message)

        return HttpResponseRedirect(
            reverse_lazy("post_detail", kwargs={"slug": self.object.post.slug})
        )

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "subdomain") and request.method == "POST":
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("//" + settings.CANONICAL_HOST)


class CommentDelete(LoginRequiredMixin, DeleteView):
    model = models.Comment
    success_message = "comment deleted"

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, self.success_message % self.object.__dict__)
        return HttpResponseRedirect(
            reverse("post_detail", kwargs={"slug": self.kwargs["slug"]})
        )

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if request.user != comment.post.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class BlogImport(LoginRequiredMixin, FormView):
    form_class = forms.UploadTextFilesForm
    template_name = "main/blog_import.html"
    success_url = reverse_lazy("blog_index")

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("file")
        if form.is_valid():
            for f in files:
                try:
                    content = f.read().decode("utf-8")
                except (UnicodeDecodeError, ValueError):
                    form.add_error("file", "File is not valid UTF-8.")
                    return self.form_invalid(form)

                models.Post.objects.create(
                    title=f.name,
                    slug=util.get_post_slug(f.name, request.user),
                    body=content,
                    owner=request.user,
                    published_at=None,
                )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def image_raw(request, slug, extension):
    image = models.Image.objects.filter(slug=slug).first()
    if not image or extension != image.extension:
        raise Http404()
    return HttpResponse(image.data, content_type="image/" + image.extension)


class ImageList(LoginRequiredMixin, FormView):
    form_class = forms.UploadImagesForm
    template_name = "main/image_list.html"
    success_url = reverse_lazy("image_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = models.Image.objects.filter(owner=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("file")
        if form.is_valid():
            for f in files:
                name_ext_parts = f.name.rsplit(".", 1)
                name = name_ext_parts[0].replace(".", "-")
                self.extension = name_ext_parts[1].casefold()
                if self.extension == "jpg":
                    self.extension = "jpeg"
                data = f.read()

                # file limit 6MB but say it's 5MB
                if len(data) > 6 * 1000 * 1000:
                    form.add_error("file", "File too big. Limit is 5MB.")
                    return self.form_invalid(form)

                self.slug = str(uuid.uuid4())[:8]
                models.Image.objects.create(
                    name=name,
                    data=data,
                    extension=self.extension,
                    owner=request.user,
                    slug=self.slug,
                )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        # if ?raw=true in url, return to image_raw instead of image_list
        if (
            len(self.request.FILES.getlist("file")) == 1
            and self.request.GET.get("raw") == "true"
        ):
            return reverse("image_raw", args=(self.slug, self.extension))
        else:
            return str(self.success_url)  # success_url may be lazy

    def form_invalid(self, form):
        # if ?raw=true in url, return form error as string
        if (
            len(self.request.FILES.getlist("file")) == 1
            and self.request.GET.get("raw") == "true"
        ):
            return HttpResponseBadRequest(" ".join(form.errors["file"]))
        else:
            return super().form_invalid(form)


class ImageDetail(LoginRequiredMixin, DetailView):
    model = models.Image

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # find posts that use this image
        context["used_by_posts"] = []
        for post in models.Post.objects.filter(owner=self.request.user):
            if "/images/" + self.object.filename in post.body:
                context["used_by_posts"].append(post)

        return context

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()
        if request.user != image.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class ImageUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Image
    fields = ["name"]
    success_message = "image updated"

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()
        if request.user != image.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class ImageDelete(LoginRequiredMixin, DeleteView):
    model = models.Image
    success_url = reverse_lazy("image_list")

    def dispatch(self, request, *args, **kwargs):
        image = self.get_object()
        if request.user != image.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class PageList(LoginRequiredMixin, ListView):
    model = models.Page

    def get_queryset(self):
        return models.Page.objects.filter(owner=self.request.user)


class PageCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = models.Page
    fields = ["title", "slug", "is_hidden", "body"]
    success_message = "'%(title)s' was created"

    def form_valid(self, form):
        if form.cleaned_data.get("slug") in denylist.DISALLOWED_PAGE_SLUGS:
            form.add_error("slug", "This slug is not allowed as a page slug.")
            return self.render_to_response(self.get_context_data(form=form))

        if models.Page.objects.filter(
            owner=self.request.user, slug=form.cleaned_data.get("slug")
        ).exists():
            form.add_error("slug", "This slug is already defined as one of your pages.")
            return self.render_to_response(self.get_context_data(form=form))

        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class PageDetail(DetailView):
    model = models.Page

    def get_queryset(self):
        queryset = models.Page.objects.filter(owner__username=self.request.subdomain)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request, "subdomain"):
            context["blog_user"] = self.request.blog_user
            context["pages"] = models.Page.objects.filter(
                owner__username=self.request.subdomain, is_hidden=False
            )

        # do not record analytic if post is authed user's
        if (
            self.request.user.is_authenticated
            and self.request.user == self.object.owner
        ):
            return context
        models.AnalyticPage.objects.create(
            user=self.request.blog_user, path=self.request.path.strip("/")
        )

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


class PageUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Page
    fields = ["title", "slug", "is_hidden", "body"]
    success_message = "page updated"

    def get_queryset(self):
        queryset = models.Page.objects.filter(owner__username=self.request.subdomain)
        return queryset

    def form_valid(self, form):
        if (
            models.Page.objects.filter(
                owner=self.request.user, slug=form.cleaned_data.get("slug")
            )
            .exclude(id=self.object.id)
            .exists()
        ):
            form.add_error("slug", "This slug is already defined as one of your pages.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if request.user != page.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class PageDelete(LoginRequiredMixin, DeleteView):
    model = models.Page
    success_url = reverse_lazy("page_list")

    def get_queryset(self):
        queryset = models.Page.objects.filter(owner__username=self.request.subdomain)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if request.user != page.owner:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class WebringUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.User
    fields = [
        "webring_name",
        "webring_url",
        "webring_prev_url",
        "webring_next_url",
    ]
    template_name = "main/webring.html"
    success_message = "webring settings updated"
    success_url = reverse_lazy("dashboard")

    def get_object(self):
        return models.User.objects.get(pk=self.request.user.id)


class AnalyticList(LoginRequiredMixin, TemplateView):
    template_name = "main/analytic_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_list"] = models.Post.objects.filter(owner=self.request.user)
        context["page_list"] = models.Page.objects.filter(owner=self.request.user)
        return context


def populate_analytics_context(context, date_25d_ago, current_date, day_counts):
    context["date_25d_ago"] = date_25d_ago
    context["analytics_per_day"] = {}
    current_x_offset = 0

    # transform day_counts into dict with date as key
    count_per_day = defaultdict(int)
    highest_day_count = 1
    for item in day_counts:
        count_per_day[item["created_at"].date()] += item["id__count"]

        # find day with the most analytics counts (i.e. visits)
        if highest_day_count < count_per_day[item["created_at"].date()]:
            highest_day_count = count_per_day[item["created_at"].date()]

    # calculate analytics count and percentages for each day
    while date_25d_ago <= current_date:
        # normalize day count to percentage for svg drawing
        count_percent = 1  # keep lowest value to 1 so as it's visible
        if highest_day_count != 0 and count_per_day[current_date] != 0:
            count_percent = count_per_day[current_date] * 100 / highest_day_count

        context["analytics_per_day"][current_date] = {
            "count_approx": util.get_approx_number(count_per_day[current_date]),
            "count_exact": count_per_day[current_date],
            "x_offset": current_x_offset,
            "count_percent": count_percent,
            "negative_count_percent": 100 - count_percent,
        }
        current_date = current_date - timedelta(days=1)
        current_x_offset += 20

    return context


class AnalyticPostDetail(LoginRequiredMixin, DetailView):
    model = models.Post
    template_name = "main/analytic_detail.html"
    slug_url_kwarg = "post_slug"

    def get_queryset(self):
        queryset = models.Post.objects.filter(owner=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.title

        # calculate dates
        current_date = timezone.now().date()
        date_25d_ago = timezone.now().date() - timedelta(days=24)

        # get all counts for the last 25 days
        day_counts = (
            models.AnalyticPost.objects.filter(
                post=self.object, created_at__gt=date_25d_ago
            )
            .values("created_at")
            .annotate(Count("id"))
        )

        return populate_analytics_context(
            context=context,
            date_25d_ago=date_25d_ago,
            current_date=current_date,
            day_counts=day_counts,
        )


class AnalyticPageDetail(LoginRequiredMixin, DetailView):
    template_name = "main/analytic_detail.html"

    def get_object(self):
        # our object is annotated with counts for the last 25 days
        date_25d_ago = timezone.now().date() - timedelta(days=24)
        return (
            models.AnalyticPage.objects.filter(
                user=self.request.user,
                path=self.kwargs["page_path"],
                created_at__gt=date_25d_ago,
            )
            .values("created_at")
            .annotate(Count("id"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.kwargs["page_path"]

        # calculate dates
        current_date = timezone.now().date()
        date_25d_ago = current_date - timedelta(days=24)

        return populate_analytics_context(
            context=context,
            date_25d_ago=date_25d_ago,
            current_date=current_date,
            day_counts=self.object,
        )


class Notification(SuccessMessageMixin, FormView):
    form_class = forms.NotificationForm
    template_name = "main/notification.html"
    success_url = reverse_lazy("index")
    success_message = "%(email)s will now receive new post notifications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog_user"] = self.request.blog_user
        return context

    def form_valid(self, form):
        # handle case already subscribed
        if models.Notification.objects.filter(
            blog_user=self.request.blog_user,
            email=form.cleaned_data.get("email"),
            is_active=True,
        ).exists():
            form.add_error(
                "email",
                f"This email is already subscribed for {self.request.blog_user.blog_title}.",
            )
            return self.render_to_response(self.get_context_data(form=form))

        # handle case subscribed but not active
        if models.Notification.objects.filter(
            blog_user=self.request.blog_user,
            email=form.cleaned_data.get("email"),
            is_active=False,
        ).exists():
            notification = models.Notification.objects.get(
                blog_user=self.request.blog_user, email=form.cleaned_data.get("email")
            )
            notification.is_active = True
            notification.save()
            return super().form_valid(form)

        # handle normal case email does not exist
        self.object = form.save(commit=False)
        self.object.blog_user = self.request.blog_user
        self.object.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "subdomain"):
            # check if newsletter is enabled for this blog_user
            if not models.User.objects.get(username=request.subdomain).notifications_on:
                return redirect("index")
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("index")


class NotificationUnsubscribe(SuccessMessageMixin, FormView):
    form_class = forms.NotificationForm
    template_name = "main/notification_unsubscribe.html"
    success_url = reverse_lazy("index")
    success_message = "%(email)s will stop receiving post notifications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog_user"] = self.request.blog_user
        return context

    def form_valid(self, form):
        notification = models.Notification.objects.get(
            blog_user=self.request.blog_user,
            email=form.cleaned_data.get("email"),
        )
        notification.is_active = False
        notification.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, "subdomain"):
            return super().dispatch(request, *args, **kwargs)
        else:
            if request.user.is_authenticated:
                subdomain = request.user.username
                return redirect(
                    f"//{subdomain}.{settings.CANONICAL_HOST}{request.path}"
                )
            else:
                return redirect("index")

        return super().dispatch(request, *args, **kwargs)


def notification_unsubscribe_key(request, unsubscribe_key):
    # handle lack of subdomain
    if not hasattr(request, "subdomain"):
        return redirect("index")

    if models.Notification.objects.filter(unsubscribe_key=unsubscribe_key).exists():
        notification = models.Notification.objects.get(unsubscribe_key=unsubscribe_key)
        email = notification.email
        notification.delete()
        return render(
            request,
            "main/notification_unsubscribe_success.html",
            {
                "blog_user": request.blog_user,
                "unsubscribed": True,
                "email": email,
            },
        )
    else:
        return render(
            request,
            "main/notification_unsubscribe_success.html",
            {
                "blog_user": request.blog_user,
                "unsubscribed": False,
            },
        )


class NotificationList(LoginRequiredMixin, ListView):
    model = models.Notification

    def get_queryset(self):
        return models.Notification.objects.filter(
            blog_user=self.request.user, is_active=True
        ).order_by("id")


class NotificationRecordList(LoginRequiredMixin, ListView):
    model = models.NotificationRecord

    def get_queryset(self):
        return models.NotificationRecord.objects.filter(
            notification__blog_user=self.request.user
        ).select_related("post", "notification")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["notificationrecord_list_unsent"] = (
            context["notificationrecord_list"]
            .filter(sent_at__isnull=True)
            .order_by("post", "is_canceled")  # order needed for {% regroup %}
        )

        # keep a list of records too old to show
        to_exclude = []
        for nr in context["notificationrecord_list_unsent"]:
            two_days_ago = timezone.now().date() - timedelta(days=2)
            if nr.is_canceled and nr.post.published_at < two_days_ago:
                to_exclude.append(nr.id)
                continue

        # exclude too old records
        context["notificationrecord_list_unsent"] = context[
            "notificationrecord_list_unsent"
        ].exclude(id__in=to_exclude)

        for nr in context["notificationrecord_list_unsent"]:

            # if post was deleted, delete nr as well
            if nr.post is None:
                nr.delete()
                continue

            # do not show if post is not published
            if not nr.post.published_at:
                nr.scheduled_at = None
                continue

            # show scheduled day as the next one after publication date
            nr.scheduled_at = nr.post.published_at + timedelta(days=1)

        context["notificationrecord_list_sent"] = (
            context["notificationrecord_list"]
            .filter(sent_at__isnull=False)
            .filter(post__isnull=False)  # do not show nr for deleted posts
        )
        return context


class NotificationRecordDelete(LoginRequiredMixin, DeleteView):
    model = models.Post
    success_url = reverse_lazy("notificationrecord_list")
    success_message = "email to '%(email)s' canceled"

    def get_queryset(self):
        queryset = models.NotificationRecord.objects.filter(
            notification__blog_user__username=self.request.user.username
        )
        return queryset

    def form_valid(self, form):
        self.object.is_canceled = True
        self.object.save()
        messages.success(
            self.request, self.success_message % self.object.notification.__dict__
        )
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def dispatch(self, request, *args, **kwargs):
        notificationrecord = self.get_object()
        if request.user != notificationrecord.notification.blog_user:
            raise PermissionDenied()

        if notificationrecord.sent_at:
            messages.error(
                request, "bad news — this notification email has already been sent :/"
            )
            return redirect("notificationrecord_list")

        return super().dispatch(request, *args, **kwargs)


def comparisons(request):
    return render(request, "main/comparisons.html")


def modus(request):
    return render(request, "main/modus.html")


def transparency(request):
    monthly_revenue = models.User.objects.filter(is_premium=True).count() * 9 / 12
    published_posts = models.Post.objects.filter(published_at__isnull=False).count()

    updated_posts = models.Post.objects.filter(
        updated_at__gt=datetime.now() - timedelta(days=30)
    ).select_related("owner")
    active_users = len({post.owner.id for post in updated_posts})

    one_month_ago = timezone.now() - timedelta(days=30)
    active_nonnew_users = len(
        {
            post.owner.id
            for post in updated_posts
            if post.owner.date_joined < one_month_ago
        }
    )
    revenue_co2 = monthly_revenue * 0.05

    # calc new users and chart data
    new_users_per_day_qs = (
        models.User.objects.annotate(date=TruncDay("date_joined"))
        .values("date")
        .annotate(user_count=Count("id"))
        .order_by("-date")[:25]
    )
    new_users_per_day = {}
    current_x_offset = 0
    # find day with the most counts (so that we can normalise the rest)
    highest_day_count = 1
    for nu in new_users_per_day_qs:
        if highest_day_count < nu["user_count"]:
            highest_day_count = nu["user_count"]
    for nu in new_users_per_day_qs:
        # normalize day count to percentage for svg drawing
        count_percent = 1  # keep lowest value to 1 (1px) so that it's visible
        if highest_day_count != 0 and nu["user_count"] != 0:
            count_percent = nu["user_count"] * 100 / highest_day_count

        new_users_per_day[nu["date"]] = {
            "count": nu["user_count"],
            "x_offset": current_x_offset,
            "count_percent": count_percent,
            "negative_count_percent": 100 - count_percent,
        }
        current_x_offset += 20

    return render(
        request,
        "main/transparency.html",
        {
            "users": models.User.objects.all().count(),
            "premium_users": models.User.objects.filter(is_premium=True).count(),
            "posts": models.Post.objects.all().count(),
            "pages": models.Page.objects.all().count(),
            "active_users": active_users,
            "active_nonnew_users": active_nonnew_users,
            "published_posts": published_posts,
            "monthly_revenue": monthly_revenue,
            "revenue_co2": revenue_co2,
            "new_users_per_day": new_users_per_day,
        },
    )


def sitemap(request):
    if not hasattr(request, "subdomain"):
        raise Http404()

    subdomain = request.subdomain

    sitemaps = {
        "static": StaticSitemap(),
        "posts": PostSitemap(subdomain),
        "pages": PageSitemap(subdomain),
    }

    return DjSitemapView(request, sitemaps)


def privacy(request):
    return render(request, "main/privacy.html")


def guides_markdown(request):
    return render(request, "main/guides_markdown.html")


def guides_images(request):
    return render(request, "main/guides_images.html")


def guides_comments(request):
    return render(
        request,
        "main/guides_comments.html",
        {
            "comments_moderation_on": settings.COMMENTS_MODERATION,
        },
    )


def atua_users(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    updated_posts = models.Post.objects.filter(
        updated_at__gte=datetime.now() - timedelta(days=30)
    ).select_related("owner")
    active_users = {post.owner for post in updated_posts}
    one_month_ago = timezone.now() - timedelta(days=30)
    active_nonnew_users = {
        post.owner for post in updated_posts if post.owner.date_joined < one_month_ago
    }

    return render(
        request,
        "main/atua_users.html",
        {
            "users": models.User.objects.all(),
            "new_users": models.User.objects.filter(date_joined__gte=one_month_ago),
            "premium_users": models.User.objects.filter(is_premium=True),
            "grandfather_users": models.User.objects.filter(is_grandfathered=True),
            "active_users": active_users,
            "active_nonnew_users": active_nonnew_users,
        },
    )


def atua_posts(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    one_month_ago = timezone.now() - timedelta(days=30)
    return render(
        request,
        "main/atua_posts.html",
        {
            "new_posts": models.Post.objects.filter(created_at__gte=one_month_ago)
            .select_related("owner")
            .order_by("-created_at"),
            "edited_posts": models.Post.objects.filter(updated_at__gte=one_month_ago)
            .select_related("owner")
            .order_by("-updated_at"),
        },
    )


def atua_pages(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    one_month_ago = timezone.now() - timedelta(days=30)
    return render(
        request,
        "main/atua_pages.html",
        {
            "new_pages": models.Page.objects.filter(created_at__gte=one_month_ago)
            .select_related("owner")
            .order_by("-created_at"),
            "edited_pages": models.Page.objects.filter(updated_at__gte=one_month_ago)
            .select_related("owner")
            .order_by("-updated_at"),
        },
    )


def atua_comments(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    one_month_ago = timezone.now() - timedelta(days=30)
    return render(
        request,
        "main/atua_comments.html",
        {
            "non_approved_comments": models.Comment.objects.filter(
                is_approved=False
            ).order_by("-id"),
            "recently_approved_comments": models.Comment.objects.filter(
                is_approved=True, created_at__gte=one_month_ago
            ),
        },
    )


class AtuaCommentApprove(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = models.Comment
    fields = ["is_approved"]
    template_name = "main/atua_comment_approve.html"
    success_url = reverse_lazy("atua_comments")
    success_message = "comment approved"

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_approved = True
        self.object.save()

        # inform blog_user
        post_url = util.get_protocol() + self.object.post.get_absolute_url()
        body = f"Someone commented on your post: {self.object.post.title}\n"
        body += "\nComment follows:\n"
        body += "\n" + self.object.body + "\n"
        body += f"\n---\nSee at {post_url}\n"
        mail.send_mail(
            subject=f"New comment for on post: {self.object.post.title}",
            message=body,
            from_email=settings.NOTIFICATIONS_FROM_EMAIL,
            recipient_list=[self.object.post.owner.email],
        )

        return HttpResponseRedirect(reverse("atua_comments"))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class AtuaCommentDelete(LoginRequiredMixin, DeleteView):
    model = models.Comment
    success_message = "comment deleted"
    template_name = "main/atua_comment_delete.html"

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, self.success_message % self.object.__dict__)
        return HttpResponseRedirect(reverse("atua_comments"))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)
