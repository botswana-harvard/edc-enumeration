import sys

from django import forms
from django.contrib import messages
from django.core.management.color import color_style
from django.forms.forms import Form
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView

from edc_base.utils import get_utcnow
from edc_base.view_mixins import EdcBaseViewMixin
from edc_dashboard.view_mixins import AppConfigViewMixin
from enumeration.views.dashboard_view import DashboardViewMixin
from household.models import HouseholdStructure
from member.exceptions import CloneError, EnumerationRepresentativeError
from member.models import HouseholdMember

style = color_style()


class CloneForm(Form):

    members = forms.MultipleChoiceField()


class CloneMembersViewMixin:

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
        imported_names = []
        for key in self.request.POST:
            if key.startswith('member'):
                try:
                    household_member = HouseholdMember.objects.get(
                        pk=self.request.POST.get(key))
                except HouseholdMember.DoesNotExist as e:
                    msg = 'Failed to import member.<br>Got {}\n'.format(e)
                    messages.add_message(request, messages.ERROR, msg)
                    sys.stdout.write(
                        style.ERROR(msg))
                    sys.stdout.flush()
                else:
                    try:
                        clone = household_member.clone(
                            household_structure=household_structure,
                            report_datetime=get_utcnow(),
                            user_created=request.user.username)
                    except CloneError as e:
                        msg = mark_safe('Unable to import {}.<br>Got \'{}\'\n'.format(
                            household_member.first_name, e))
                        messages.add_message(request, messages.ERROR, msg)
                        sys.stdout.write(
                            style.ERROR(msg))
                        sys.stdout.flush()
                    else:
                        try:
                            clone.save()
                        except EnumerationRepresentativeError as e:
                            msg = ('Unable to import {}.<br>Got \'{}\'\n'.format(
                                household_member.first_name, e))
                            messages.add_message(request, messages.ERROR, msg)
                            sys.stdout.write(
                                style.ERROR(msg))
                            sys.stdout.flush()
                        else:
                            imported_names.append(clone.first_name)
        if imported_names:
            msg = 'Successfully import {}.'.format(
                ', '.join(imported_names))
            messages.add_message(request, messages.SUCCESS, msg)
        url = reverse(
            self.dashboard_url_name,
            kwargs={
                'household_identifier': household_identifier,
                'survey_schedule': survey_schedule,
            })
        return HttpResponseRedirect(url)


class CloneMembersView(CloneMembersViewMixin,
                       AppConfigViewMixin, DashboardViewMixin,
                       EdcBaseViewMixin, TemplateView):
    app_config_name = 'enumeration'
