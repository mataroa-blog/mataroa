from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from main import models


def user_list(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    # handle simple case first
    if not request.GET.get("mode"):
        user_list = models.User.objects.all()[:1000].prefetch_related("post_set")
        return render(
            request,
            "main/adminextra_user_list.html",
            {
                "user_list": user_list,
                "TRANSLATE_API_URL": settings.TRANSLATE_API_URL,
                "TRANSLATE_API_TOKEN": settings.TRANSLATE_API_TOKEN,
                "DEBUG": "true" if settings.DEBUG else "false",
            },
        )

    mode = request.GET.get("mode").split(",")
    user_list = models.User.objects.all()
    if "noapprove" in mode:
        user_list = user_list.filter(is_approved=False).order_by("-id")
    if "noempty" in mode:
        user_list = (
            user_list.annotate(count=Count("post"))
            .filter(count__gt=0)
            .order_by("-id")
            .prefetch_related("post_set")
        )
    if "premium" in mode:
        user_list = user_list.filter(is_premium=True).order_by("-id")
    if "reverse" in mode:
        user_list = user_list.order_by("id")

    return render(
        request,
        "main/adminextra_user_list.html",
        {
            "user_list": user_list[:1000],
            "TRANSLATE_API_URL": settings.TRANSLATE_API_URL,
            "TRANSLATE_API_TOKEN": settings.TRANSLATE_API_TOKEN,
            "DEBUG": "true" if settings.DEBUG else "false",
        },
    )


def user_approve(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    referer_url = request.META.get("HTTP_REFERER")

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = True
        user.save()
        messages.add_message(request, messages.SUCCESS, "user has been approved")
        return redirect(referer_url)

    raise Http404()


def user_unapprove(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    referer_url = request.META.get("HTTP_REFERER")

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = False
        user.save()
        messages.add_message(request, messages.SUCCESS, "user is no longer approved")
        return redirect(referer_url)

    raise Http404()
