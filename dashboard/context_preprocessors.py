from django.conf import settings


def dashboard_settings(request):
    return {
        "menu_show_switch_item": settings.DASHBOARD_ALLOW_MULTIPLE_SYSTEMS,
        "csrf_cookie_name": settings.CSRF_COOKIE_NAME
    }
