from django.conf import settings
from django.db import models


class System(models.Model):
    api_user = models.ForeignKey(settings.AUTH_USER_MODEL, help_text="User on whose behalf API calls are made to AmCAT")
    project_id = models.PositiveIntegerField(help_text="AmCAT project this dashboard is linked to", null=True)
    project_name = models.TextField(null=True)

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()
