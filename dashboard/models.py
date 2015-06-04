import datetime
import json

from django.conf import settings
import requests
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models

EPOCH = datetime.datetime.fromtimestamp(0)

class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"

    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))

    email = models.EmailField(_('email address'), blank=False, unique=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    amcat_token = models.TextField(null=True)
    amcat_username = models.TextField(null=True)

    objects = UserManager()

    class Meta:
        app_label = "dashboard"


class Query(models.Model):
    amcat_query_id = models.IntegerField(db_index=True)
    amcat_project_id = models.IntegerField()

    amcat_name = models.TextField()
    amcat_parameters = models.TextField()

    # To prevent bombarding the AmCAT servers with request, we cache results. These
    # caches might be refreshed by a cronjob or manually
    cache = models.TextField(null=True)
    cache_timestamp = models.DateTimeField(default=EPOCH)
    cache_mimetype = models.TextField(null=True)
    cache_uuid = models.TextField(null=True)

    def get_parameters(self):
        return json.loads(self.amcat_parameters)

    def get_articleset_ids(self):
        return list(map(int, self.get_parameters()["articlesets"]))

    def get_script(self):
        return self.get_parameters()["script"]

    def get_output_type(self):
        return self.get_parameters()["output_type"]

    def clear_cache(self):
        self.cache = None
        self.cache_timestamp = EPOCH
        self.cache_mimetype = None
        self.cache_uuid = None

    def update(self):
        url = "http://preview.amcat.nl/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(project=self.amcat_project_id, query=self.amcat_query_id)

        response = requests.get(url, cookies={
            "sessionid": settings.SESSION_ID
        })

        data = json.loads(response.content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]
