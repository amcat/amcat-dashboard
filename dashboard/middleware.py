import re
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import redirect
from dashboard.models import System, Page

from urllib.parse import urlencode

EXEMPT_URLS = [re.compile(expr) for expr in getattr(settings, "LOGIN_EXEMPT_URLS", ())]


def in_exempt_urls(path_info, exempt_urls=tuple(EXEMPT_URLS)):
    return any(m.match(path_info.lstrip('/')) for m in exempt_urls)


class LoginRequiredMiddleware:
    """
    Source: https://djangosnippets.org/snippets/1179/

    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).

    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """
    def process_request(self, request):
        if not request.user.is_authenticated:
            if not in_exempt_urls(request.path_info):
                redirect_url = "{}?{}".format(reverse("dashboard-login"), urlencode({"next": request.path_info}))
                return HttpResponseRedirect(redirect_url)


class APITokenNeededMiddleware:
    exempt_urls = (
        re.compile(reverse("dashboard:token-setup").lstrip('/')),
        re.compile(reverse("dashboard:system-list").lstrip('/')),
        *EXEMPT_URLS
    )

    def process_request(self, request):
        if in_exempt_urls(request.path_info, self.exempt_urls):
            # Do nothing when on login / register page
            return None

        if not request.user.is_authenticated:
            return None

        has_token = System.objects.exclude(amcat_token=None).exists()

        if not has_token:
            # no systems exist, a superuser must set one up
            return redirect(reverse("dashboard:token-setup"))

        if request.user.system is None:
            try:
                request.user.system = System.objects.get()
            except System.MultipleObjectsReturned:
                # multiple systems exist, let the user choose
                return redirect(reverse("dashboard:system-list"))
            else:
                request.user.save()

        return None




class MethodOverrideMiddleware(object):
    allowed_http_methods = ['GET', 'HEAD', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'PATCH']
    http_header = "HTTP_X_HTTP_METHOD_OVERRIDE"

    # https://pypi.python.org/pypi/django-method-override/0.1.0
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.method != 'POST':
            return
        method = self._get_method_override(request)
        if method in self.allowed_http_methods:
            setattr(request, method, request.POST.copy())
            request.method = method

    def _get_method_override(self, request):
        method = request.META.get(self.http_header)
        return method and method.upper()