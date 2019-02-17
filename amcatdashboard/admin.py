from django.contrib.admin import site, ModelAdmin
from dashboard.models import User

class DashboardUserAdmin(ModelAdmin):
    exclude = ("password",)

site.register(User, DashboardUserAdmin)
