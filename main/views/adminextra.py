from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from main import models


def user_list(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    return render(
        request,
        "main/adminextra_user_list.html",
        {
            "user_list": models.User.objects.all()[:1000].prefetch_related("post_set"),
        },
    )


def user_approve(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = True
        user.save()
        messages.add_message(request, messages.SUCCESS, "user has been approved")
        return redirect("adminextra_user_list")

    return render(
        request,
        "main/adminextra_user_approve.html",
        {
            "user": models.User.objects.get(id=user_id),
        },
    )


def user_unapprove(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = False
        user.save()
        messages.add_message(request, messages.SUCCESS, "user is no longer approved")
        return redirect("adminextra_user_list")

    return render(
        request,
        "main/adminextra_user_unapprove.html",
        {
            "user": models.User.objects.get(id=user_id),
        },
    )
