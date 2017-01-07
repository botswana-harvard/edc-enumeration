import sys

from django.apps import AppConfig as DjangoAppConfig
from django.core.management.color import color_style

style = color_style()


class AppConfig(DjangoAppConfig):
    name = 'enumeration'
    list_template_name = None
    enumeration_dashboard_base_html = 'edc_base/base.html'

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
