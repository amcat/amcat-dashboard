import re
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import redirect
from dashboard.models import System, Page

try:
    # Python 3.X
    from urllib.parse import urlencode
except ImportError:
    # Python 2.7
    from urllib import urlencode

EXEMPT_URLS = [re.compile(expr) for expr in getattr(settings, "LOGIN_EXEMPT_URLS", ())]

def in_exempt_urls(path_info):
    return any(m.match(path_info.lstrip('/')) for m in EXEMPT_URLS)


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
        if not request.user.is_authenticated():
            if not in_exempt_urls(request.path_info):
                redirect_url = "{}?{}".format(reverse("account_login"), urlencode({"next": request.path_info}))
                return HttpResponseRedirect(redirect_url)


class APITokenNeededMiddleware:
    def process_request(self, request):
        if in_exempt_urls(request.path_info):
            # Do nothing when on login / register page
            return None

        if request.path_info == reverse("dashboard:token-setup"):
            return None

        if request.user.is_authenticated():
            try:
                system = System.objects.get(user=request.user)
            except System.DoesNotExist:
                token = None
            else:
                token = system.amcat_token

            if not request.user.is_superuser:
                return None

            if not token:
                return redirect(reverse("dashboard:token-setup"))

