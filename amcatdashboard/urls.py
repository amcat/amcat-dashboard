from django.conf.urls import include, url
from django.views.generic import RedirectView
from dashboard.views.account import SignupView

urlpatterns = [
    url(r"^account/signup/$", SignupView.as_view(), name="account_signup"),
    url(r'^$', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    url(r"^account/", include("account.urls")),
    url(r"^dashboard/", include("dashboard.urls", namespace="dashboard"))
]
