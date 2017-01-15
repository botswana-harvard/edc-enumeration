from django.apps import apps as django_apps

from household.views import HouseholdAppConfigViewMixin


class EnumerationAppConfigViewMixin(HouseholdAppConfigViewMixin):

    app_config_name = 'enumeration'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            subject_listboard_url_name=django_apps.get_app_config('bcpp_subject').listboard_url_name,
            subject_dashboard_url_name=django_apps.get_app_config('bcpp_subject').dashboard_url_name,
            enumeration_dashboard_url_name=django_apps.get_app_config('enumeration').dashboard_url_name,
        )
        return context
