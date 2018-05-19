from django.conf import settings


def menu_settings(request):
    return {
        "menu_show_switch_item": settings.DASHBOARD_ALLOW_MULTIPLE_SYSTEMS
    }
