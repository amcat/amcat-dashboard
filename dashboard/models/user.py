import datetime
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

    amcat_token = models.TextField(null=True)
    amcat_username = models.TextField(null=True)

    objects = UserManager()

    class Meta:
        app_label = "dashboard"