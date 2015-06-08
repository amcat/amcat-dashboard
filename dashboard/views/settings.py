from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import FormView
from dashboard.models import System


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
