def subdomain_middleware(get_response):
    def middleware(request):
        host = request.META.get("HTTP_HOST")
        if host and len(host.split(".")) == 3:
            request.subdomain = host.split(".")[0]

        response = get_response(request)
        return response

    return middleware
