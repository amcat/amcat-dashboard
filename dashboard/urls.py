from django.conf.urls import url
from dashboard.views.dashboard import index

urlpatterns = [
    url("^$", index)
]
