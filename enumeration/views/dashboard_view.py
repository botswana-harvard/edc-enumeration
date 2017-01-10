from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_base.utils import get_utcnow
from edc_constants.constants import ALIVE, YES, MALE

from household.models.household_log import HouseholdLog
from household.models.household_log_entry import HouseholdLogEntry
from household.models.household_structure.household_structure import HouseholdStructure
from member.constants import HEAD_OF_HOUSEHOLD, AVAILABLE
from member.models import HouseholdHeadEligibility, HouseholdMember, RepresentativeEligibility, HouseholdInfo
from member.models.household_member.utils import is_minor, is_adult
from member.participation_status import ParticipationStatus
from survey.site_surveys import site_surveys
from survey.survey import DummySurvey


class Button:
    def __init__(self, obj, household_structure=None):
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
            self.household_member = obj.household_member
        except AttributeError:
            self.household_member = None
        try:
            self.household_structure = obj.household_structure
        except AttributeError:
            self.household_structure = household_structure


class DashboardView(EdcBaseViewMixin, TemplateView):

    template_name = 'enumeration/dashboard.html'
    paginate_by = 4
    base_html = 'bcpp/base.html'

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
        member.is_minor = is_minor(member.age_in_years)
        member.is_adult = is_adult(member.age_in_years)
        if member.refused:
            member.done = True
        return member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app_config = django_apps.get_app_config('enumeration')
        self.today = context.get('today')  # for tests
        if context.get('household_member'):
            self.household_identifier = context.get(
                'household_member').household_structure.household.household_identifier
            survey = context.get('household_member').household_structure.survey_object
        else:
            self.household_identifier = context.get('household_identifier')
            survey = site_surveys.get_survey_from_field_value(
                context.get('survey')) or DummySurvey()
        survey_objects = site_surveys.current_surveys
        try:
            self.household_structure = HouseholdStructure.objects.get(
                household__household_identifier=self.household_identifier,
                survey=survey.field_value)
        except HouseholdStructure.DoesNotExist:
            self.household_structure = None
            self.household_log = None
            self.household_log_entries = None
            self.household_members = None
        else:
            self.household_log = HouseholdLog.objects.get(
                household_structure=self.household_structure)
            self.household_log_entries = HouseholdLogEntry.objects.filter(
                household_log__household_structure=self.household_structure).order_by(
                    '-report_datetime')
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
            survey_objects=survey_objects,
            survey=survey,
            map_area=survey.map_area_display,
            household_log=self.household_log,
            household_log_entries=self.household_log_entries,
            household_members=self.household_members,
            household_structure=self.household_structure,
            current_household_log_entry=self.current_household_log_entry,
            can_add_members=self.can_add_members,
            eligibility_buttons=self.eligibility_buttons(self.household_structure)
        )
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new members."""
        if not self.representative_eligibility or not self.current_household_log_entry:
            return False
        return True

    def eligibility_buttons(self, household_structure):

        # representative_eligibility
        eligibility_buttons = []
        btn = Button(self.representative_eligibility or RepresentativeEligibility(),
                     household_structure=household_structure)
        # can edit anytime, but can only add if have todays log...
        if not self.current_household_log_entry and btn.add:
            btn.disabled = True
        eligibility_buttons.append(btn)

        # head_of_household_eligibility
        btn = Button(self.head_of_household_eligibility or HouseholdHeadEligibility(),
                     household_structure=household_structure)
        btn = Button(self.head_of_household_eligibility or HouseholdHeadEligibility(),
                     household_structure=household_structure)
        if not btn.household_member:
            btn.household_member = self.head_of_household
        # only enable if hoh exists
        if not btn.household_member:
            btn.disabled = True
        # can edit anytime, but can only add if have todays log...
        if (not self.current_household_log_entry and btn.add) or not self.household_members:
            btn.disabled = True
        eligibility_buttons.append(btn)

        # household_info
        try:
            household_info = HouseholdInfo.objects.get(household_structure=self.household_structure)
        except HouseholdInfo.DoesNotExist:
            household_info = HouseholdInfo()
        if not self.representative_eligibility:
            btn.disabled = True
        if not self.current_household_log_entry and btn.add:
            btn.disabled = True
        btn = Button(household_info, household_structure=household_structure)
        eligibility_buttons.append(btn)
        return eligibility_buttons

    @property
    def current_household_log_entry(self):
        """Return current household log entry model instance, or none."""
        current_household_log_entry = None
        today = self.today or get_utcnow()
        if self.household_log_entries:
            obj = self.household_log_entries.all().order_by('report_datetime').last()
            try:
                if obj.report_datetime.date() == today.date():
                    current_household_log_entry = obj
            except AttributeError:
                pass
        return current_household_log_entry

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
