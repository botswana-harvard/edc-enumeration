import arrow

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import ALIVE, YES, MALE

from household.models.household_log import HouseholdLog
from household.models.household_log_entry import HouseholdLogEntry
from household.models.household_structure.household_structure import HouseholdStructure
from member.constants import HEAD_OF_HOUSEHOLD, AVAILABLE
from member.models import HouseholdHeadEligibility, HouseholdMember, RepresentativeEligibility
from member.participation_status import ParticipationStatus

from .utils import survey_from_label
from survey.site_surveys import site_surveys


class Button:
    def __init__(self, obj):
        self.name = obj._meta.label_lower
        self.verbose_name = obj._meta.verbose_name
        self.url_name = 'member:member_admin:{}'.format('_'.join(obj._meta.label_lower.split('.')))
        if obj.id:
            self.id = str(obj.id)
            self.url_name = self.url_name + '_change'
            self.add = False
        else:
            self.id = None
            self.url_name = self.url_name + '_add'
            self.add = True
        self.disabled = False
        try:
            self.member = obj.household_member
        except AttributeError:
            self.member = None


class DashboardView(EdcBaseViewMixin, TemplateView):

    template_name = 'enumeration/dashboard.html'
    paginate_by = 4

    def __init__(self, **kwargs):
        self.household_identifier = None
        self.survey = None
        super().__init__(**kwargs)

    def member_wrapper(self, member):
        member.participation_status = ParticipationStatus(member).participation_status
        member.get_participation_status_display = ParticipationStatus(
            member).get_participation_status_display()
        if member.participation_status == AVAILABLE:
            member.get_participation_status_display = None
        member.final_status_pending = ParticipationStatus(member).final_status_pending
        if member.refused:
            member.done = True
        return member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app_config = django_apps.get_app_config('enumeration')
        self.today = context.get('today', arrow.utcnow())  # for tests
        self.household_identifier = context.get('household_identifier')
        survey = survey_from_label(context.get('survey'))
        survey_objects = site_surveys.surveys
        try:
            self.household_structure = HouseholdStructure.objects.get(
                household__household_identifier=self.household_identifier,
                survey=survey.label)
        except HouseholdStructure.DoesNotExist:
            self.household_structure = None
            self.household_log = None
            self.household_log_entries = None
            self.household_members = None
        else:
            self.household_log = HouseholdLog.objects.get(household_structure=self.household_structure)
            self.household_log_entries = HouseholdLogEntry.objects.filter(
                household_log__household_structure=self.household_structure).order_by('-report_datetime')
            self.household_members = HouseholdMember.objects.filter(
                household_structure=self.household_structure).order_by('first_name')
            self.household_members = [self.member_wrapper(obj) for obj in self.household_members]
        context.update(
            site_header=admin.site.site_header,
            ALIVE=ALIVE,
            YES=YES,
            MALE=MALE,
            enumeration_dashboard_base_html=app_config.enumeration_dashboard_base_html,
            navbar_selected='enumeration',
            survey_breadcrumbs=survey.survey_breadcrumbs,
            survey_objects=survey_objects,
            map_area=survey.map_area_display,
            household_log=self.household_log,
            household_log_entries=self.household_log_entries,
            household_members=self.household_members,
            household_structure=self.household_structure,
            todays_household_log_entry=self.todays_household_log_entry,
            can_add_members=self.can_add_members,
            eligibility_buttons=self.eligibility_buttons
        )
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new members."""
        if not self.representative_eligibility or not self.todays_household_log_entry:
            return False
        return True

    @property
    def eligibility_buttons(self):

        eligibility_buttons = []
        btn = Button(self.representative_eligibility or RepresentativeEligibility())
        # can edit anytime, but can only add if have todays log...
        if not self.todays_household_log_entry and btn.add:
            btn.disabled = True
        eligibility_buttons.append(btn)
        btn = Button(self.head_of_household_eligibility or HouseholdHeadEligibility())
        if not btn.member:
            btn.member = self.head_of_household
        # can edit anytime, but can only add if have todays log...
        if (not self.todays_household_log_entry and btn.add) or not self.household_members:
            btn.disabled = True
        eligibility_buttons.append(btn)
        return eligibility_buttons

    @property
    def todays_household_log_entry(self):
        """Return "today's" household log entry model instance, or none."""
        todays_household_log_entry = None
        try:
            obj = self.household_log_entries.order_by('report_datetime').last()
            if obj.report_datetime.date() == self.today.date():
                todays_household_log_entry = obj
        except AttributeError:
            pass
        return todays_household_log_entry

    @property
    def head_of_household(self):
        """Returns the household member model instance that is the Head of Household or None."""
        try:
            obj = HouseholdMember.objects.get(
                household_structure=self.household_structure,
                relation=HEAD_OF_HOUSEHOLD)
        except HouseholdMember.DoesNotExist:
            obj = None
        return obj

    @property
    def head_of_household_eligibility(self):
        """Return the head of household eligibility model instance or None."""
        try:
            obj = HouseholdHeadEligibility.objects.get(
                household_member=self.head_of_household)
        except HouseholdHeadEligibility.DoesNotExist:
            obj = None
        return obj

    @property
    def representative_eligibility(self):
        """Return the representative eligibility model instance."""
        try:
            obj = RepresentativeEligibility.objects.get(
                household_structure=self.household_structure)
        except RepresentativeEligibility.DoesNotExist:
            obj = None
        return obj
