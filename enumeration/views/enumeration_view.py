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

from .utils import survey_from_label

app_config = django_apps.get_app_config('enumeration')


class SearchPlotForm(SearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_action = reverse('enumeration:list_url')


class EnumerationView(EdcBaseViewMixin, TemplateView, SearchViewMixin, FormView):

    form_class = SearchPlotForm
    template_name = app_config.list_template_name
    paginate_by = 10
    list_url = 'enumeration:list_url'
    search_model = HouseholdStructure
    url_lookup_parameters = [
        'id',
        'survey',
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
        HouseholdMember = django_apps.get_model(*'member.householdmember'.split('.'))
        for obj in qs:
            obj.plot_identifier = obj.household.plot.plot_identifier
            obj.household_identifier = obj.household.household_identifier
            _, obj.survey_year, obj.survey_name, obj.community_name = obj.survey.split('.')
            obj.community_name = ' '.join(obj.community_name.split('_'))
            obj.members = HouseholdMember.objects.filter(
                household_structure=obj)
            results.append(obj)
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = survey_from_label(context.get('survey'))
        context.update(
            navbar_selected='enumeration',
            survey_breadcrumbs=survey.survey_breadcrumbs,
            map_area=survey.map_area_display)
        return context
