from django.http import Http404
from django.shortcuts import render

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
