from amcatclient import AmcatAPI
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import FormView
from dashboard.models import System



class SetupTokenForm(forms.ModelForm):
    hostname = forms.CharField(widget=forms.TextInput, initial=System._meta.get_field_by_name("hostname")[0].default)

    amcat_username = forms.CharField()
    amcat_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(SetupTokenForm, self).clean()

        username = cleaned_data.get("amcat_username")
        password = cleaned_data.get("amcat_password")
        hostname = cleaned_data.get("hostname")

        if not (username and password and hostname):
            return cleaned_data

        try:
            AmcatAPI(host=hostname, user=username, password=password)
        except:
            raise ValidationError("Could not authenticate using given username and password. The credentials might be wrong, or the AmCAT server is not responding.")

        return cleaned_data

    def save(self, commit=True):
        system = super(SetupTokenForm, self).save(commit=False)

        amcat_username = self.cleaned_data["amcat_username"]
        amcat_password = self.cleaned_data["amcat_password"]
        system.set_token(amcat_username, amcat_password)

        if commit:
            system.save()

        return system

    class Meta:
        model = System
        fields = ("hostname", "project_id")

class SetupTokenView(FormView):
    form_class = SetupTokenForm
    template_name = "dashboard/setup_token.html"

    def get_form(self, **kwargs):
        form_class = self.get_form_class()

        try:
            return form_class(instance=System.load(), **self.get_form_kwargs())
        except System.DoesNotExist:
            return form_class(**self.get_form_kwargs())

    def form_valid(self, form):
        form.save()
        return super(SetupTokenView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:index")


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = System
        exclude = ("project_name",)

class SystemSettingsView(FormView):
    form_class = SystemSettingsForm
    template_name = "dashboard/system.html"

    def get_form_kwargs(self):
        return dict(super().get_form_kwargs(), instance=System.load())

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, "Form saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:system-settings")
