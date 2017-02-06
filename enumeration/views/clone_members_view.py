import sys

from django import forms
from django.core.management.color import color_style
from django.forms.forms import Form
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.views.generic.edit import FormView

from edc_base.utils import get_utcnow
from edc_dashboard.view_mixins import AppConfigViewMixin, DashboardViewMixin

from enumeration.views.dashboard_view import DashboardView
from household.models import HouseholdStructure
from member.exceptions import CloneError, EnumerationRepresentativeError
from member.models import HouseholdMember

style = color_style()


class CloneForm(Form):

    members = forms.MultipleChoiceField()


class CloneMembersView(DashboardView, FormView):

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
                except HouseholdMember.DoesNotExist as e:
                    sys.stdout.write(
                        style.ERROR('Failed to clone member. Got {}'.format(e)))
                    sys.stdout.flush()
                else:
                    try:
                        clone = household_member.clone(
                            household_structure=household_structure,
                            report_datetime=get_utcnow(),
                            user_created=request.user.username)
                    except CloneError as e:
                        sys.stdout.write(
                            style.ERROR(
                                'Failed to clone member. {}. Got {}'.format(
                                    household_member.first_name, e)))
                        sys.stdout.flush()
                    else:
                        try:
                            clone.save()
                        except EnumerationRepresentativeError as e:
                            sys.stdout.write(
                                style.ERROR(
                                    'Failed to clone member. {}. Got {}'.format(
                                        household_member.first_name, e)))
                        sys.stdout.flush()
        url = reverse(
            self.dashboard_url_name,
            kwargs={
                'household_identifier': household_identifier,
                'survey_schedule': survey_schedule,
            })
        return HttpResponseRedirect(url)
