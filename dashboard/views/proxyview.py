import logging
from urllib.parse import urlparse

from django.views.generic import TemplateView


class ProxyView(TemplateView):
    template_name = "dashboard/proxy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not "target" in self.request.GET:
            raise ValueError("No target for proxy")
        href =self.request.GET['target']
        parsed = urlparse(href)
        this_domain = self.request.META['HTTP_HOST'].split(":")[0]
        proxy_domain = parsed.netloc.split(":")[0]
        if proxy_domain not in ('', this_domain):
            logging.warning(f"Cannot proxy, netloc: {parsed.netloc}, this_domain: {this_domain}")
            raise ValueError(f"Cannot proxy to {href}")
        context['href'] = href
        context['hide_menu'] = self.request.user.system.hide_menu and not self.request.user.is_superuser

        return context

