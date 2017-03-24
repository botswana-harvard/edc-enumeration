from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from edc_base.view_mixins import EdcBaseViewMixin
from edc_dashboard.views import ListboardView as BaseListboardView
from edc_dashboard.view_mixins import AppConfigViewMixin

from household.models import HouseholdStructure
from household.view_mixins import HouseholdQuerysetViewMixin
from plot.view_mixins import PlotQuerysetViewMixin

from .wrappers import HouseholdStructureWithLogEntryWrapper


class ListboardView(AppConfigViewMixin, EdcBaseViewMixin,
                    HouseholdQuerysetViewMixin, PlotQuerysetViewMixin,
                    BaseListboardView):

    app_config_name = 'enumeration'
    navbar_item_selected = 'enumeration'
    model = HouseholdStructure
    model_wrapper_class = HouseholdStructureWithLogEntryWrapper
    paginate_by = 10
    plot_queryset_lookups = ['household', 'plot']
    household_queryset_lookups = ['household']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset_filter_options(self, request, *args, **kwargs):
        options = super().get_queryset_filter_options(request, *args, **kwargs)
        if kwargs.get('survey_schedule'):
            options.update(
                {'survey_schedule': kwargs.get('survey_schedule')})
        return options
