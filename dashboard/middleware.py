import re
from urllib.parse import urlencode
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import redirect
from dashboard.models import System

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

        if request.user.is_authenticated():
            system = System.load()

            assert system.api_user, "No user account linked to System.api_user. This " \
                                    "should have happened while registering the first " \
                                    "user!"

            assert system.api_user.is_superuser, "System.api_user should be a superuser"

            if system.api_user.amcat_token is not None:
                # Token set, so we can do nothing
                return None

            if system.api_user == request.user:
                return redirect(reverse("dashboard:amcat-settings"))

            return redirect(reverse("dashboard:empty"))

