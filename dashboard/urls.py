from django.conf.urls import url
from dashboard.views.dashboard import index, AmCATSettingsView

urlpatterns = [
    url("^$", index, name="index"),
    url("^amcat$", AmCATSettingsView.as_view(), name="amcat-settings")
]
