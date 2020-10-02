from timeit import default_timer as timer

from django.conf import settings
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect

from main import models


def host_middleware(get_response):
    def middleware(request):
        host = request.META.get("HTTP_HOST")

        # no http Host header in testing
        if not host:
            return get_response(request)

        host_parts = host.split(".")
        canonical_parts = settings.CANONICAL_HOST.split(".")

        if host == settings.CANONICAL_HOST:
            # if on mataroa.blog, don't set request.subdomain, and just return
            return get_response(request)
        elif (
            len(host_parts) == 3
            and host_parts[1] == canonical_parts[0]  # should be "mataroa"
            and host_parts[2] == canonical_parts[1]  # should be "blog"
        ):
            # if on <subdomain>.mataroa.blog, and set subdomain to given
            # validation will happen inside views
            # the indexes are different because settings.CANONICAL_HOST has no subdomain
            request.subdomain = host_parts[0]

            # if subdomain is 'random', let it through
            if request.subdomain == "random":
                return get_response(request)

            # check if subdomain exists
            if models.User.objects.filter(username=request.subdomain).exists():
                # if not logged in, always redirect to the custom domain
                blog_user = models.User.objects.get(username=request.subdomain)
                if not request.user.is_authenticated and blog_user.custom_domain:
                    return redirect("//" + blog_user.custom_domain + request.path_info)
            else:
                raise Http404()
        elif models.User.objects.filter(custom_domain=host).exists():
            # custom domain case
            request.subdomain = models.User.objects.get(custom_domain=host).username
        else:
            return HttpResponseBadRequest()

        return get_response(request)

    return middleware


def speed_middleware(get_response):
    def middleware(request):
        request.start = timer()

        response = get_response(request)

        end = timer()
        response["X-Request-Time"] = end - request.start
        print("X-Request-Time:", response["X-Request-Time"])
        return response

    return middleware
