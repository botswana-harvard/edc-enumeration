from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_search.forms import SearchForm
from edc_search.view_mixins import SearchViewMixin

from household.models import HouseholdStructure
from household.utils import survey_from_label
from household.views import HouseholdStructureResultWrapper
from edc_constants.constants import MALE

app_config = django_apps.get_app_config('enumeration')


class SearchPlotForm(SearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_action = reverse('enumeration:list_url')


class ResultWrapper(HouseholdStructureResultWrapper):

    @property
    def querystring(self):
        return [
            'next={},household_structure'.format('enumeration:list_url'),
            'household_structure={}'.format(self.id),
            'household_log={}'.format(self.household_log.id),
        ]


class EnumerationView(EdcBaseViewMixin, TemplateView, SearchViewMixin, FormView):

    form_class = SearchPlotForm
    template_name = app_config.list_template_name
    paginate_by = 10
    list_url = 'enumeration:list_url'
    search_model = HouseholdStructure
    url_lookup_parameters = [
        'id',
        'survey',
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

    def queryset_wrapper(self, qs):
        results = []
        for obj in qs:
            results.append(ResultWrapper(obj))
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = survey_from_label(context.get('survey'))
        context.update(
            navbar_selected='enumeration',
            MALE=MALE,
            survey_breadcrumbs=survey.survey_breadcrumbs,
            map_area=survey.map_area_display)
        return context
