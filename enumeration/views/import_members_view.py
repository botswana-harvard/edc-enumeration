from django import forms
from django.views.generic.edit import FormView
from django.forms.forms import Form
from edc_dashboard.view_mixins.app_config_view_mixin import AppConfigViewMixin
from edc_base.view_mixins import EdcBaseViewMixin
from edc_dashboard.view_mixins.dashboard_view_mixin import DashboardViewMixin
from survey.view_mixins import SurveyViewMixin
from household.views.mixins import HouseholdViewMixin
from pprint import pprint
from django.views.generic.base import RedirectView
from django.urls.base import reverse
from enumeration.views.dashboard_view import DashboardView
from django.shortcuts import redirect
from django.http.response import HttpResponseRedirect
from member.models.household_member.household_member import HouseholdMember
from household.models.household_structure.household_structure import HouseholdStructure
from edc_base.utils import get_utcnow
from dateutil.relativedelta import relativedelta
from member.exceptions import CloneError


class ImportForm(Form):

    members = forms.MultipleChoiceField()


class ImportMembersView(DashboardView, FormView):

    def get_success_url(self):
        return reverse(self.dashboard_url_name,
                       kwargs={
                           'household_identifier': self.household_identifier,
                           'survey_schedule': self.survey_schedule
                       })

    def post(self, request, *args, **kwargs):
        household_identifier = kwargs.get('household_identifier')
        survey_schedule = kwargs.get('survey_schedule')
        household_structure = HouseholdStructure.objects.get(
            household__household_identifier=household_identifier,
            survey_schedule=survey_schedule)
        for key in self.request.POST:
            if key.startswith('member'):
                try:
                    household_member = HouseholdMember.objects.get(
                        pk=self.request.POST.get(key))
                except HouseholdMember.DoesNotExist:
                    pass
                else:
                    try:
                        clone = household_member.clone(
                            household_structure=household_structure,
                            report_datetime=get_utcnow(),
                            user_created=request.user.username,
                        )
                    except CloneError:
                        pass
                    else:
                        clone.save()

        url = reverse(
            self.dashboard_url_name,
            kwargs={
                'household_identifier': household_identifier,
                'survey_schedule': survey_schedule
            })
        return HttpResponseRedirect(url)
