from django.conf.urls import url

from dashboard.views import dashboard_edit
from dashboard.views import dashboard_view
from dashboard.views import settings

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
    url("^system_settings$", settings.SystemSettingsView.as_view(), name="system-settings"),
    url("^synchronise_queries$", dashboard_edit.synchronise_queries, name="synchronise-queries"),
    url("^save_rows/(?P<page_id>[0-9]+)$", dashboard_edit.save_rows, name="save-rows"),
    url("^page/(?P<page_id>[0-9]+)$", dashboard_view.DashboardPageView.as_view(), name="view-page"),
    url("^menu/$", dashboard_edit.menu, name="edit-menu"),
    url("^save_menu/$", dashboard_edit.save_menu, name="save-menu"),
]
