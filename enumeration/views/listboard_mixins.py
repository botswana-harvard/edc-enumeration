from django.apps import apps as django_apps
from django.db.models import Q

from edc_dashboard.view_mixins import FilteredListViewMixin as BaseFilteredListViewMixin
from edc_search.view_mixins import SearchViewMixin as BaseSearchViewMixin

from household.models import HouseholdStructure

from .wrappers import HouseholdStructureWithLogEntryWrapper


class SearchViewMixin(BaseSearchViewMixin):

    search_model = HouseholdStructure
    search_model_wrapper_class = HouseholdStructureWithLogEntryWrapper
    search_queryset_ordering = '-modified'

    def search_options(self, search_term, **kwargs):
        q = (
            Q(household__household_identifier__icontains=search_term) |
            Q(household__plot__plot_identifier__icontains=search_term) |
            Q(user_created__iexact=search_term) |
            Q(user_modified__iexact=search_term))
        options = {}
        return q, options


class FilteredListViewMixin(BaseFilteredListViewMixin):

    filter_model = HouseholdStructure
    filtered_model_wrapper_class = HouseholdStructureWithLogEntryWrapper
    filtered_queryset_ordering = '-modified'
    url_lookup_parameters = [
        ('id', 'id'),
        ('survey_schedule', 'survey_schedule'),
        ('household_structure', 'id'),
        ('household_identifier', 'household__household_identifier'),
        ('plot_identifier', 'household__plot__plot_identifier')]

    @property
    def filtered_queryset(self):
        plot_identifier = django_apps.get_app_config(
            'plot').anonymous_plot_identifier
        return self.filter_model.objects.exclude(
            household__plot__plot_identifier=plot_identifier).order_by(
                self.filtered_queryset_ordering)
