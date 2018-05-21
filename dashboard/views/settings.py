from amcatclient import AmcatAPI
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed, Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import FormView, ListView
from dashboard.models import System, User, HighchartsTheme


class TokenWidget(forms.TextInput):
    """
    A TextInput with a "request token" button.
    """
    button_text = _('Request token')
    template_name = 'dashboard/widgets/token.html'
    hostname_input_name = "hostname"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['button_text'] = self.button_text
        context['hostname_input_name'] = self.hostname_input_name
        return context


class SetupTokenForm(forms.ModelForm):
    hostname = forms.CharField(widget=forms.TextInput, initial=System._meta.get_field("hostname").default)

    amcat_token = forms.CharField(required=False,
                                  help_text=_("Click the button to request a token, or instead, enter username and password:"), widget=TokenWidget)
    amcat_username = forms.CharField(required=False)
    amcat_password = forms.CharField(required=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(SetupTokenForm, self).clean()

        if not settings.DASHBOARD_ALLOW_MULTIPLE_SYSTEMS and System.objects.exists():
            raise ValidationError(_("The server is setup for one system only, no other projects may be created."))

        username = cleaned_data.get("amcat_username")
        password = cleaned_data.get("amcat_password")
        hostname = cleaned_data.get("hostname")
        token = cleaned_data.get("amcat_token")

        if not (hostname and (bool(token) ^ bool(username and password))):
            raise ValidationError(_("Invalid credentials: either request a token or enter a username or password."))
            return cleaned_data

        authkwargs = {"token": token} if token else {"username": username, "password": password}

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


class SystemAddView(FormView):
    form_class = SetupTokenForm
    template_name = "dashboard/setup_token.html"

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            raise SuspiciousOperation(_("%(user)s is not a superuser. You need to be a superuser to access this page.") %
                                      {"user": self.request.user.name})
        system = form.save()
        self.request.user.system = system
        self.request.user.save()
        return super(SystemAddView, self).form_valid(form)

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
        return {
            "systems_pings": [(system, system.ping()) for system in System.objects.all()],
            **kwargs
        }

    def form_valid(self, form):
        self.request.user.system = form.cleaned_data['system']
        self.request.user.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:system-list")


class SystemSettingsForm(forms.ModelForm):
    hostname = forms.CharField()
    amcat_token = forms.CharField(widget=TokenWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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
        messages.add_message(self.request, messages.SUCCESS, _("Form saved."))
        return super(SystemSettingsView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:system-list")


class SystemMixin:
    @property
    def system(self):
        try:
            return System.objects.get(pk=self.kwargs['system_id'])
        except System.DoesNotExist:
            raise Http404


class SystemThemeListView(SystemMixin, ListView):
    model = HighchartsTheme
    template_name = 'dashboard/theme_list.html'

    def get_queryset(self):
        return self.model.objects.filter(system=self.system)


