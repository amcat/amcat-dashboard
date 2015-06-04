import json

from django.conf import settings
import requests
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models


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
    amcat_query_id = models.IntegerField()
    amcat_project_id = models.IntegerField()

    amcat_name = models.TextField()
    amcat_parameters = models.TextField()

    def get_parameters(self):
        return json.loads(self.amcat_parameters)

    def update(self, user):
        url = "http://preview.amcat.nl/api/v4/projects/{project}/querys/{query}/?format=json"
        url = url.format(project=self.amcat_project_id, query=self.amcat_query_id)

        response = requests.get(url, cookies={
            "sessionid": settings.SESSION_ID
        })

        data = json.loads(response.content.decode('utf-8'))
        self.amcat_name = data["name"]
        self.amcat_parameters = data["parameters"]
