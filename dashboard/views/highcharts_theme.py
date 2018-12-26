from django import forms
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from dashboard.models import HighchartsTheme, System
from dashboard.views.settings import SystemMixin


class SystemThemeMixin:
    queryset = HighchartsTheme.objects.all()
    fields = ('system', 'name', 'colors', 'y_axis_line_width', 'y_axis_has_line_color', 'y_label_has_line_color')

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

    def get_success_url(self):
        return reverse('dashboard:system-theme-list', args=(self.system.id,))

    def get_initial(self):
        initial = super().get_initial()
        return dict(initial)


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
