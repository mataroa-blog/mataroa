from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from main import models


def host_middleware(get_response):
    def middleware(request):
        host = request.META.get("HTTP_HOST")

        # probably in testing there is no Host http header
        if not host:
            response = get_response(request)
            return response

        host_parts = host.split(".")
        canonical_parts = settings.CANONICAL_HOST.split(".")

        if host == settings.CANONICAL_HOST:
            # if on mataroa.blog, don't set request.subdomain, and just return
            response = get_response(request)
            return response
        elif (
            len(host_parts) == 3
            and host_parts[1] == canonical_parts[0]  # should be "mataroa"
            and host_parts[2] == canonical_parts[1]  # should be "blog"
        ):
            # if on <subdomain>.mataroa.blog, and set subdomain to given
            # validation will happen inside views
            # the indexes are different because settings.CANONICAL_HOST has no subdomain
            request.subdomain = host_parts[0]
        elif models.User.objects.filter(custom_domain=host).exists():
            # custom domain case
            request.subdomain = models.User.objects.get(custom_domain=host).username
        else:
            raise SuspiciousOperation()

        response = get_response(request)
        return response

    return middleware
