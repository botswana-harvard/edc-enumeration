import sys

from django.apps import AppConfig as DjangoAppConfig
from django.core.management.color import color_style

style = color_style()


class AppConfig(DjangoAppConfig):
    name = 'enumeration'
    listboard_template_name = 'enumeration/listboard.html'
    listboard_url_name = 'enumeration:listboard_url'
    dashboard_url_name = 'enumeration:dashboard_url'
    enumeration_dashboard_base_html = 'edc_base/base.html'

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
