import os
from binascii import unhexlify

from django import forms
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.http import etag
from django.views.generic import CreateView, UpdateView, DeleteView

from dashboard.models import HighchartsTheme, System
from dashboard.views.settings import SystemMixin


class SystemThemeMixin:
    queryset = HighchartsTheme.objects.all()
    fields = ('system', 'name', 'colors')

    def get_initial(self):
        return dict(super().get_initial(), system=self.system.id)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields['name'].widget = forms.TextInput()
        form.fields['system'].widget = forms.HiddenInput()
        form.fields['system'].queryset = System.objects.filter(pk=self.system.id)
        return form


class SystemThemeCreateView(SystemMixin, SystemThemeMixin, CreateView):
    template_name = 'dashboard/theme_form.html'
    theme_default = None

    def get_success_url(self):
        return reverse('dashboard:system-theme-list', args=(self.system.id,))

    def _try_get_default(self):
        if self.theme_default is not None:
            return self.theme_default

        try:
            path = os.path.dirname(__file__)
            self.theme_default = open('{}/data/theme_default.scss'.format(path), mode="r").read()
            return self.theme_default
        except FileNotFoundError:
            return ""

    def get_initial(self):
        initial = super().get_initial()
        return dict(initial, theme=self._try_get_default())


class SystemThemeEditView(SystemMixin, SystemThemeMixin, UpdateView):
    template_name = 'dashboard/theme_form.html'
    pk_url_kwarg = 'theme_id'

    def get_success_url(self):
        return reverse('dashboard:system-theme-list', args=(self.system.id,))


class SystemThemeDeleteView(SystemMixin, DeleteView):
    template_name = 'dashboard/theme_confirm_delete.html'
    queryset = HighchartsTheme.objects.all()
    pk_url_kwarg = 'theme_id'

    def get_success_url(self):
        return reverse('dashboard:system-theme-list', args=(self.system.id,))
