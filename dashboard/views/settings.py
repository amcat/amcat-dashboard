from collections.__init__ import OrderedDict

import requests
from amcatclient import AmcatAPI
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseModelFormSet
from django.http import HttpResponseNotAllowed, Http404, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView, ListView, DeleteView
from dashboard.models import System, User, HighchartsTheme
from dashboard.models.dashboard import Filter


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
    hostname = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "https://"}))

    amcat_token = forms.CharField(required=True,
                                  help_text=_("Click the 'Request Token' button to request a token from AmCAT"), widget=TokenWidget)

    def clean(self):
        cleaned_data = super(SetupTokenForm, self).clean()

        if not settings.DASHBOARD_ALLOW_MULTIPLE_SYSTEMS and System.objects.exists():
            raise ValidationError(_("The server is setup for one system only, no other projects may be created."))

        hostname = cleaned_data.get("hostname")
        token = cleaned_data.get("amcat_token")

        authkwargs = {"token": token}

        try:
            AmcatAPI(host=hostname, **authkwargs)
        except Exception as e:
            print(e)
            raise ValidationError(_("Could not authenticate using given token. The credentials might be wrong, or the AmCAT server is not responding."))

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


class SystemMixin:
    @property
    def system(self):
        try:
            return System.objects.get(pk=self.kwargs['system_id'])
        except System.DoesNotExist:
            raise Http404


class SystemDeleteView(DeleteView):
    model = System
    pk_url_kwarg = "system_id"
    def get_success_url(self):
        return reverse('dashboard:system-list')

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
    hostname = forms.CharField(disabled=True)
    project_id = forms.CharField(disabled=True)
    amcat_token = forms.CharField(widget=TokenWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    class Meta:
        model = System
        exclude = ("project_name",)

class SystemSettingsView(SystemMixin, FormView):
    form_class = SystemSettingsForm
    template_name = "dashboard/system.html"

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs.get('system_id') is None:
            if request.method != "GET":
                raise HttpResponseNotAllowed(['GET'])
            return redirect('dashboard:system-settings', request.user.system.id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(SystemSettingsView, self).get_form_kwargs()

        try:
            system = System.objects.get(id=self.kwargs.get('system_id'))
        except System.DoesNotExist:
            raise Http404(_("System does not exist"))

        if 'amcat_token' in self.request.GET:
            kwargs.setdefault('initial', {})
            kwargs['initial']['amcat_token'] = self.request.GET['amcat_token']
        return dict(kwargs, instance=system)

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, _("Form saved."))
        return super(SystemSettingsView, self).form_valid(form)

    def get_success_url(self):
        return self.request.get_raw_uri()


class SystemThemeListView(SystemMixin, ListView):
    model = HighchartsTheme
    template_name = 'dashboard/theme_list.html'

    def get_queryset(self):
        return self.model.objects.filter(system=self.system)


class BaseFilterFormSet(BaseModelFormSet):
    def __init__(self, *args, system, **kwargs):
        super().__init__(*args, **kwargs)
        self.system = system

    def save_new(self, form, commit=True):
        form.instance.system = self.system
        super().save_new(form, commit=commit)

    def _construct_form(self, *args, **kwargs):
        form = super()._construct_form(*args, **kwargs)
        form.fields['field'].widget.attrs['placeholder'] = 'field'
        form.fields['value'].widget.attrs['placeholder'] = 'value'
        return form


FilterFormSet = modelformset_factory(Filter, exclude=("system",), extra=2, max_num=1000, can_delete=True,
                                     formset=BaseFilterFormSet)


class FiltersEditView(SystemMixin, FormView):
    form_class = FilterFormSet
    template_name = "dashboard/edit_filters.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['queryset'] = Filter.objects.filter(system=self.system)
        kwargs['system'] = self.system
        return kwargs

    def form_valid(self, formset):
        formset.save()
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse('dashboard:edit-filters', args=[self.kwargs['system_id']])
