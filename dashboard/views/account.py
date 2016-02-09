from __future__ import absolute_import

from account import forms as account_forms, views
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import FormView

from dashboard.models import User, System


class SignupForm(account_forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        del self.fields["username"]

class LoginView(views.LoginView):
    form_class = account_forms.LoginEmailForm

class SignupView(views.SignupView):
    """The first user who registers is promoted to superuser"""
    form_class = SignupForm

    def get_context_data(self, **kwargs):
        context_data = super(SignupView, self).get_context_data(**kwargs)
        context_data["first_signup"] = User.objects.count() == 0
        return context_data

    def create_user(self, form, commit=True, **kwargs):
        user = super(SignupView, self).create_user(form, commit=False, **kwargs)

        if not User.objects.exists():
            user.is_superuser = True

        if commit:
            user.save()

        return user

    def generate_username(self, form):
        return "This value is not used."


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ()


class AmCATSettingsView(FormView):
    form_class = UserForm
    template_name = "dashboard/amcat_settings.html"

    def get_success_url(self):
        return reverse("dashboard:amcat-settings")

    def get_context_data(self, **kwargs):
        return dict(super(AmCATSettingsView, self).get_context_data(**kwargs), system=System.load())

    def get_form_kwargs(self):
        return dict(super(AmCATSettingsView, self).get_form_kwargs(), instance=self.request.user)

    def form_valid(self, form):
        super(AmCATSettingsView, self).form_valid(form)
        form.save()
        return redirect(reverse("dashboard:index"))
