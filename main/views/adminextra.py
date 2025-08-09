from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from urllib.parse import urlencode

from main import models


def user_cards(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    if hasattr(request, "subdomain"):
        return redirect(f"//{settings.CANONICAL_HOST}{request.path}")

    user_list = (
        models.User.objects.annotate(count=Count("post"))
        .filter(count__gt=0, is_approved=False)
        .order_by("?")
    )
    user = user_list.first()
    post_list = models.Post.objects.filter(owner=user)
    post_list_halfpoint = post_list.count() // 2 if post_list.count() > 1 else 1
    post_list_a = post_list[:post_list_halfpoint]
    post_list_b = post_list[post_list_halfpoint:]
    return render(
        request,
        "main/adminextra_user_single.html",
        {
            "user": user,
            "user_count": user_list.count(),
            "post_list_a": post_list_a,
            "post_list_b": post_list_b,
            "TRANSLATE_API_URL": settings.TRANSLATE_API_URL,
            "TRANSLATE_API_TOKEN": settings.TRANSLATE_API_TOKEN,
            "DEBUG": "true" if settings.DEBUG else "false",
        },
    )


def user_list(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    if hasattr(request, "subdomain"):
        return redirect(f"//{settings.CANONICAL_HOST}{request.path}")

    # build base queryset
    user_qs = models.User.objects.all()

    # handle filters via mode param
    mode_param = request.GET.get("mode")
    if mode_param:
        mode = mode_param.split(",")
        if "noapprove" in mode:
            user_qs = user_qs.filter(is_approved=False)
        if "noempty" in mode:
            user_qs = user_qs.annotate(count=Count("post")).filter(count__gt=0)
        if "premium" in mode:
            user_qs = user_qs.filter(is_premium=True)
        # ordering
        if "reverse" in mode:
            user_qs = user_qs.order_by("id")
        else:
            user_qs = user_qs.order_by("-id")
    else:
        # default ordering for simple case
        user_qs = user_qs.order_by("-id")
    current_modes = mode if mode_param else []

    # prefetch posts for listed users
    user_qs = user_qs.prefetch_related("post_set")

    # pagination
    per_page_default = 100
    try:
        per_page = int(request.GET.get("per_page", per_page_default))
    except (TypeError, ValueError):
        per_page = per_page_default
    paginator = Paginator(user_qs, per_page)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # preserve existing non-page query params in pagination links
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    # Build clickable filter links
    def link_for_modes(modes_list: list[str]) -> str:
        query: dict[str, str] = {}
        # preserve per_page
        if per_page != per_page_default:
            query["per_page"] = str(per_page)
        if modes_list:
            query["mode"] = ",".join(modes_list)
        return f"?{urlencode(query)}" if query else "?"

    all_filter_keys = ["noapprove", "noempty", "premium", "reverse"]
    filters = []
    for key in all_filter_keys:
        is_active = key in current_modes
        if is_active:
            new_modes = [m for m in current_modes if m != key]
        else:
            new_modes = current_modes + [key]
        filters.append(
            {
                "key": key,
                "active": is_active,
                "url": link_for_modes(new_modes),
            }
        )
    clear_filters_url = link_for_modes([])

    return render(
        request,
        "main/adminextra_user_list.html",
        {
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": paginator.num_pages > 1,
            "user_list": page_obj.object_list,
            "querystring": querystring,
            "filters": filters,
            "clear_filters_url": clear_filters_url,
            "TRANSLATE_API_URL": settings.TRANSLATE_API_URL,
            "TRANSLATE_API_TOKEN": settings.TRANSLATE_API_TOKEN,
            "DEBUG": "true" if settings.DEBUG else "false",
        },
    )


def user_delete(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.delete()
        return JsonResponse({"ok": True})

    raise Http404()


def user_approve(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    referer_url = request.META.get("HTTP_REFERER")

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = True
        user.save()
        return JsonResponse({"ok": True})

    raise Http404()


def user_unapprove(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404()

    referer_url = request.META.get("HTTP_REFERER")

    user = get_object_or_404(models.User, id=user_id)
    if request.method == "POST":
        user.is_approved = False
        user.save()
        return JsonResponse({"ok": True})

    raise Http404()
