from __future__ import absolute_import

from account import forms as account_forms, views
from account.forms import LoginUsernameForm
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import FormView, RedirectView

from dashboard.models import User, System

import logging

class SignupForm(account_forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        del self.fields["username"]

class LoginView(views.LoginView):
    class form_class(LoginUsernameForm):
        username = forms.CharField(label="Email", max_length=500)

class SignupView(views.SignupView):
    """The first user who registers is promoted to superuser"""
    form_class = SignupForm

    def get_context_data(self, **kwargs):
        context_data = super(SignupView, self).get_context_data(**kwargs)
        context_data["first_signup"] = User.objects.count() == 0
        return context_data

    def create_user(self, form, commit=True, **kwargs):
        user = super(SignupView, self).create_user(form, commit=False, **kwargs)

        # Somehow Pinax messes this up:
        user.set_password(form.cleaned_data['password'])

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


class AmCATSettingsView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('dashboard:system-settings', args=[self.request.user.system_id])
