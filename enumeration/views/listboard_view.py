from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import MALE
from edc_dashboard.view_mixins import ListboardMixin, FilteredListViewMixin
from edc_search.view_mixins import SearchViewMixin

from household.models import HouseholdStructure
from survey import site_surveys
from survey.survey import DummySurvey

from .wrappers import HouseholdStructureWithLogEntryWrapper

app_config = django_apps.get_app_config('enumeration')


class ListBoardView(EdcBaseViewMixin, ListboardMixin, FilteredListViewMixin, SearchViewMixin):

    template_name = app_config.listboard_template_name
    listboard_url_name = app_config.listboard_url_name
    search_model = HouseholdStructure
    search_model_wrapper_class = HouseholdStructureWithLogEntryWrapper
    search_queryset_ordering = '-modified'

    filter_model = HouseholdStructure
    filtered_model_wrapper_class = HouseholdStructureWithLogEntryWrapper
    filtered_queryset_ordering = '-modified'
    url_lookup_parameters = [
        'id',
        'survey_schedule',
        ('household_structure', 'id'),
        ('household_identifier', 'household__household_identifier'),
        ('plot_identifier', 'household__plot__plot_identifier')]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def search_options(self, search_term, **kwargs):
        q = (
            Q(household__household_identifier__icontains=search_term) |
            Q(household__plot__plot_identifier__icontains=search_term) |
            Q(user_created__iexact=search_term) |
            Q(user_modified__iexact=search_term))
        options = {}
        return q, options

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey_schedule = site_surveys.get_survey_schedule_from_field_value(
            context.get('survey_schedule')) or DummySurvey()
        context.update(
            navbar_selected='enumeration',
            MALE=MALE,
            survey_schedule=survey_schedule,
            map_area=survey_schedule.map_area_display,
            plot_listboard_url_name=django_apps.get_app_config('plot').listboard_url_name,
            household_listboard_url_name=django_apps.get_app_config('household').listboard_url_name,
            member_listboard_url_name=django_apps.get_app_config('member').listboard_url_name,
            enumeration_listboard_url_name=django_apps.get_app_config('enumeration').listboard_url_name,
            enumeration_dashboard_url_name=django_apps.get_app_config('enumeration').dashboard_url_name,
        )
        return context
