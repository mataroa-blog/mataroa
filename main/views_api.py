import json

from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from main import forms, models, util


def api_docs(request):
    return render(request, "main/api_docs.html")


@require_POST
@csrf_exempt
def api_posts(request):
    # check authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        raise PermissionDenied()

    # check auth header form
    if auth_header[:7] != "Bearer ":
        raise BadRequest()

    # check token's user
    token = auth_header[7:]
    users_from_token = models.User.objects.filter(api_key=token)
    if not users_from_token:
        raise PermissionDenied()
    user = users_from_token.first()

    # validate input data
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise BadRequest()
    if "title" not in data or "body" not in data:
        raise BadRequest()

    # create new post
    slug = util.get_post_slug(data["title"], user)
    post = models.Post.objects.create(
        owner=user, title=data["title"], slug=slug, body=data["body"], published_at=None
    )

    return JsonResponse(
        {"slug": slug, "url": util.get_protocol() + post.get_absolute_url()}
    )
