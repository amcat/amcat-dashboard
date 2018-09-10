from django.conf import settings


def dashboard_settings(request):
    return {
        "global_theme": getattr(settings, 'GLOBAL_THEME', None),
        "menu_show_switch_item": settings.DASHBOARD_ALLOW_MULTIPLE_SYSTEMS,
        "csrf_cookie_name": settings.CSRF_COOKIE_NAME
    }
