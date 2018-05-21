from django.conf.urls import url

import dashboard.views.highcharts_theme
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
    url("^systems$", settings.SystemListView.as_view(), name="system-list"),
    url("^system_settings/(?P<system_id>[0-9]+)?$", settings.SystemSettingsView.as_view(), name="system-settings"),
    url("^systems/(?P<system_id>[0-9]+)/themes$", settings.SystemThemeListView.as_view(), name="system-theme-list"),
    url("^systems/(?P<system_id>[0-9]+)/themes/add$", dashboard.views.highcharts_theme.SystemThemeCreateView.as_view(), name="system-theme-add"),
    url("^systems/(?P<system_id>[0-9]+)/themes/(?P<theme_id>[0-9]+)/edit$", dashboard.views.highcharts_theme.SystemThemeEditView.as_view(), name="system-theme-edit"),
    url("^systems/(?P<system_id>[0-9]+)/themes/(?P<theme_id>[0-9]+)/delete", dashboard.views.highcharts_theme.SystemThemeDeleteView.as_view(), name="system-theme-delete"),
    url("^theme/(?P<tag>[a-zA-Z0-9]+).css$", dashboard.views.highcharts_theme.get_theme, name="theme-css"),
    url("^token_setup$", settings.SystemAddView.as_view(), name="token-setup"),
    url("^synchronise_queries$", dashboard_edit.synchronise_queries, name="synchronise-queries"),
    url("^save_rows/(?P<page_id>[0-9]+)$", dashboard_edit.save_rows, name="save-rows"),
    url("^page/(?P<page_id>[0-9]+)$", dashboard_view.DashboardPageView.as_view(), name="view-page"),
    url("^page/(?P<page_slug>\w+)$", dashboard_view.DashboardPageView.as_view(), name="view-page"),
    url("^menu/$", dashboard_edit.menu, name="edit-menu"),
    url("^save_menu/$", dashboard_edit.save_menu, name="save-menu"),
]
