from amcatclient import AmcatAPI
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed, Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import FormView, ListView
from dashboard.models import System, User
from django.utils.html import format_html


class TokenWidget(forms.TextInput):
    """
    A TextInput with a "request token" button.
    """

    def render(self, name, value, attrs=None):
        input_group = '<div class="input-group">{}</div>'
        input = super().render(name, value, attrs)
        button = format_html(
            '<span class="input-group-btn">'
            '<a id="{0}-request-token" class="btn btn-primary">{1}</a>'
            '</span>'
            , name, _('Request token'))
        return format_html(input_group, input + button)


class SetupTokenForm(forms.ModelForm):
    hostname = forms.CharField(widget=forms.TextInput, initial=System._meta.get_field("hostname").default)

    amcat_token = forms.CharField(required=False,
                                  help_text=_("Click the button to request a token, or instead, enter username and password:"), widget=TokenWidget)
    amcat_username = forms.CharField(required=False)
    amcat_password = forms.CharField(required=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(SetupTokenForm, self).clean()

        username = cleaned_data.get("amcat_username")
        password = cleaned_data.get("amcat_password")
        hostname = cleaned_data.get("hostname")
        token = cleaned_data.get("amcat_token")

        if not (hostname and (bool(token) ^ bool(username and password))):
            raise ValidationError(_("Invalid credentials: either request a token or enter a username or password."))
            return cleaned_data

        authkwargs = {"token": token} if token else {"username": username, "password": password}
        print(authkwargs)
        try:
            AmcatAPI(host=hostname, **authkwargs)
        except:
            raise ValidationError(_("Could not authenticate using given username and password. The credentials might be wrong, or the AmCAT server is not responding."))

        return cleaned_data

    def save(self, commit=True):
        system = super(SetupTokenForm, self).save(commit=False)

        token = self.cleaned_data.get("amcat_token")
        if token:
            system.amcat_token = AmcatAPI(host=self.cleaned_data['hostname'], token=token).token
        else:
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('initial', {})
        if self.request.GET.get('amcat_token'):
            kwargs['initial'].update(amcat_token=self.request.GET['amcat_token'])
        if self.request.GET.get('hostname'):
            kwargs['initial'].update(hostname=self.request.GET['hostname'])
        return kwargs


class SystemSelectForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("system",)

class SystemListView(FormView):
    form_class = SystemSelectForm
    template_name = "dashboard/system_list.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return {"instance": self.request.user, **kwargs}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        return {"objects_list": System.objects.all(), **kwargs}


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = System
        exclude = ("project_name",)


class SystemSettingsView(FormView):
    form_class = SystemSettingsForm
    template_name = "dashboard/system.html"

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('system_id') is None:
            if request.method != "GET":
                raise HttpResponseNotAllowed(['GET'])
            return redirect('dashboard:system-settings', request.user.system.id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        try:
            system = System.objects.get(id=self.kwargs.get('system_id'))
        except System.DoesNotExist:
            raise Http404(_("System does not exist"))
        return dict(super(SystemSettingsView, self).get_form_kwargs(), instance=system)

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, "Form saved.")
        return super(SystemSettingsView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:system-settings")
