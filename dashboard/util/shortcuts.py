from urllib.parse import urlparse

from django.shortcuts import redirect


def redirect_referrer(request, same_origin=True, default="/"):
    """
    Redirects to the HTTP Referer header, or to `default` if the referrer is not valid.
    If `same_origin` is True, the referrer will be validated against the request's HTTP Host.

    When using a virtual host, e.g. using Nginx, make sure the Host header is set appropriately.

    TODO: verify if this works with HTTPS and/or ports other than 80
    """

    referer = request.META.get('HTTP_REFERER')

    url = urlparse(referer)
    origin_referer = (url.scheme, url.netloc)
    origin_self = (request.scheme, request.get_host())

    if referer is None or (not same_origin and origin_referer != origin_self):
        url = default
    else:
        url = referer

    return redirect(url)
