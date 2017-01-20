from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import MALE
from edc_dashboard.view_mixins import ListboardViewMixin, AppConfigViewMixin

from survey import SurveyViewMixin

from .listboard_mixins import FilteredListViewMixin, SearchViewMixin


class ListBoardView(EdcBaseViewMixin, ListboardViewMixin, AppConfigViewMixin,
                    FilteredListViewMixin, SearchViewMixin,
                    SurveyViewMixin, TemplateView, FormView):

    app_config_name = 'enumeration'
    navbar_item_selected = 'enumeration'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(MALE=MALE)
        return context
