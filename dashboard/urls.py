from django.conf.urls import url

from dashboard.views import dashboard_edit
from dashboard.views import dashboard_view

from dashboard.views.account import AmCATSettingsView


urlpatterns = [
    url("^$", dashboard_view.index, name="index"),
    url("^amcat$", AmCATSettingsView.as_view(), name="amcat-settings"),
    url("^get_saved_query_result/(?P<query_id>[0-9]+)$", dashboard_view.get_saved_query_result, name="get-saved-query-result"),
    url("^get_saved_query/(?P<query_id>[0-9]+)$", dashboard_view.get_saved_query, name="get-saved-query"),
    url("^clear_cache/(?P<query_id>[0-9]+)$", dashboard_view.clear_cache, name="clear-cache"),
    url("^empty$", dashboard_view.empty, name="empty"),
    url("^edit$", dashboard_edit.index, name="edit-index"),
    url("^edit/(?P<page_id>[0-9]+)$", dashboard_edit.page, name="edit-page"),
    url("^import_query$", dashboard_edit.import_query, name="import-query"),
]
