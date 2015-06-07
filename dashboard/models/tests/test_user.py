from django.test import TestCase
from dashboard.models import User


class TestUser(TestCase):
    def test_initial(self):
        user = User.objects.create(email="a@a", is_superuser=False)


