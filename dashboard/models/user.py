import datetime
from amcatclient import AmcatAPI

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

EPOCH = datetime.datetime.fromtimestamp(0)


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"

    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))

    email = models.EmailField(_('email address'), blank=False, unique=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    system = models.ForeignKey('dashboard.System', null=True, on_delete=models.SET_NULL)

    objects = UserManager()

    def get_api(self, host):
        return AmcatAPI(host=host, token=self.amcat_token)

    @property
    def is_staff(self):
        return self.is_superuser

    def get_short_name(self):
        return self.email.split("@")[0]
    class Meta:
        app_label = "dashboard"
