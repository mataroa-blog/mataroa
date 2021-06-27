import uuid
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.db.models import Count
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
                posts = models.Post.objects.filter(owner=request.blog_user)
            else:
                models.AnalyticPage.objects.create(user=request.blog_user, path="index")
                posts = models.Post.objects.filter(
                    owner=request.blog_user,
                    published_at__isnull=False,
                    published_at__lte=timezone.now().date(),
                ).order_by("-published_at")

            return render(
                request,
                "main/blog_index.html",
                {
                    "subdomain": request.subdomain,
                    "blog_user": request.blog_user,
                    "posts": posts,
                    "pages": models.Page.objects.filter(
                        owner=request.blog_user, is_hidden=False
                    ),
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
            context["comments"] = models.Comment.objects.filter(post=self.object)

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

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super().delete(request, *args, **kwargs)

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
    success_message = "your comment was published"

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
        self.object.post = models.Post.objects.get(
            owner__username=self.request.subdomain, slug=self.kwargs["slug"]
        )
        self.object.save()
        messages.add_message(self.request, messages.INFO, self.success_message)

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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, self.success_message % self.object.__dict__)
        return HttpResponseRedirect(
            reverse("post_detail", kwargs={"slug": kwargs["slug"]})
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
    template_name = "main/blog_webring_update.html"
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
            "count": count_per_day[current_date],
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

        context["title"] = self.object.title

        return populate_analytics_context(
            context=context,
            date_25d_ago=date_25d_ago,
            current_date=current_date,
            day_counts=day_counts,
        )


class AnalyticPageDetail(LoginRequiredMixin, DetailView):
    template_name = "main/analytic_detail.html"

    def get_object(self):
        date_25d_ago = timezone.now().date() - timedelta(days=24)
        return models.AnalyticPage.objects.filter(
            user=self.request.user,
            path=self.kwargs["page_path"],
            created_at__gt=date_25d_ago,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # calculate dates
        current_date = timezone.now().date()
        date_25d_ago = current_date - timedelta(days=24)

        # get all counts for the last 25 days
        day_counts = self.object.values("created_at").annotate(Count("id"))

        context["title"] = self.kwargs["page_path"]

        return populate_analytics_context(
            context=context,
            date_25d_ago=date_25d_ago,
            current_date=current_date,
            day_counts=day_counts,
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
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["notificationrecord_list_unsent"] = (
            context["notificationrecord_list"]
            .filter(sent_at__isnull=True)
            .order_by("post")
        )
        for nr in context["notificationrecord_list_unsent"]:
            if not nr.post.published_at:
                nr.scheduled_at = None
                continue
            nr.scheduled_at = nr.post.published_at + timedelta(days=1)

        context["notificationrecord_list_sent"] = context[
            "notificationrecord_list"
        ].filter(sent_at__isnull=False)
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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
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


def privacy(request):
    return render(request, "main/privacy.html")


def guides_markdown(request):
    return render(request, "main/guides_markdown.html")


def guides_images(request):
    return render(request, "main/guides_images.html")
