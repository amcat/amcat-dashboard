import json
from account import forms, views
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.views.generic import FormView
import requests
from dashboard.models import User


class SignupForm(forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        del self.fields["username"]

class LoginView(views.LoginView):
    form_class = forms.LoginEmailForm

class SignupView(views.SignupView):
    form_class = SignupForm

    def generate_username(self, form):
        return "This value is not used."


class UserForm(forms.ModelForm):
    amcat_token = forms.CharField(required=False)
    amcat_username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    def clean(self):
        data = super().clean()

        url = "http://preview.amcat.nl/api/v4/get_token"
        response = requests.post(url, data={
            'username': data["amcat_username"],
            'password': data["password"]
        })

        if (response.status_code != 200):
            raise ValidationError("AmCAT replied with status code {}".format(response.status_code))

        data["amcat_token"] = json.loads(response.content.decode("utf-8"))["token"]

        return data

    class Meta:
        model = User
        fields = ("amcat_token", "amcat_username")


class AmCATSettingsView(FormView):
    form_class = UserForm
    template_name = "dashboard/amcat_settings.html"

    def get_success_url(self):
        return reverse("dashboard:amcat-settings")

    def get_form_kwargs(self):
        return dict(super().get_form_kwargs(), instance=self.request.user)

    def form_valid(self, form):
        resp = super().form_valid(form)
        form.save()
        return resp