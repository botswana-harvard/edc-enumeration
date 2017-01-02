import sys

from django.apps import AppConfig as DjangoAppConfig, apps as django_apps
from django.core.management.color import color_style

style = color_style()


class AppConfig(DjangoAppConfig):
    name = 'enumeration'
    list_template_name = None

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        current_surveys = django_apps.get_app_config('survey').current_surveys
        current_mapper_name = django_apps.get_app_config('edc_map').current_mapper_name
        if current_surveys.map_area != current_mapper_name:
            sys.stdout.write(style.ERROR(
                '\nERROR: Configurations for \'edc_map\' and \'survey\' are incorrect. Expected the \'current_mapper_name\' '
                '(map_area) to correspond with \'current_survey_label\'. Got {} != {}. See AppConfig for '
                'edc_map and survey\nYou should also ensure that the \'household\' AppConfig comes after '
                '\'edc_map\' and \'survey\' in INSTALLED_APPS.\n'.format(
                    current_mapper_name, current_surveys.map_area)))
        sys.stdout.write(' * detected current surveys are:\n')
        for current_survey in current_surveys:
            sys.stdout.write('   - {}\n'.format(current_survey.label))
        sys.stdout.write(' * detected current mapper/map_area is \'{}\'\n'.format(current_mapper_name))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
