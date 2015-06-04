from django.conf.urls import url
from dashboard.views.dashboard import index, AmCATSettingsView, get_saved_query

urlpatterns = [
    url("^$", index, name="index"),
    url("^amcat$", AmCATSettingsView.as_view(), name="amcat-settings"),
    url("^get_saved_query/(?P<query_id>[0-9]+)$", get_saved_query, name="get-saved-query")
]
