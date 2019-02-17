import account.views
from django.conf.urls import include, url
from django.views.generic import RedirectView
from dashboard.views.account import SignupView, LoginView
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog
from .admin import site




urlpatterns = [
    url(r"^account/signup/$", SignupView.as_view(), name="account_signup"),
    url(r'^$', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    url(r"^account/", include("account.urls")),
    url(r"^dashboard/", include("dashboard.urls", namespace="dashboard")),
    url(r"^admin/", site.urls),
    url(r"^login/", LoginView.as_view(), name="dashboard-login"),

    url(r"^jsi18n/$", cache_page(86400)(JavaScriptCatalog.as_view()), name='javascript-catalog'),

]
