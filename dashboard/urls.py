from django.conf.urls import url
from dashboard.views.dashboard import index, AmCATSettingsView, get_saved_query_result, \
    get_saved_query, clear_cache

urlpatterns = [
    url("^$", index, name="index"),
    url("^amcat$", AmCATSettingsView.as_view(), name="amcat-settings"),
    url("^get_saved_query_result/(?P<query_id>[0-9]+)$", get_saved_query_result, name="get-saved-query-result"),
    url("^get_saved_query/(?P<query_id>[0-9]+)$", get_saved_query, name="get-saved-query"),
    url("^clear_cache/(?P<query_id>[0-9]+)$", clear_cache, name="clear-cache")
]
