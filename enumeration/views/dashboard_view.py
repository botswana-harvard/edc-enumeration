import arrow

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic import TemplateView

from edc_base.view_mixins import EdcBaseViewMixin

from household.models.household_log_entry import HouseholdLogEntry
from household.models.household_structure.household_structure import HouseholdStructure
from member.constants import HEAD_OF_HOUSEHOLD
from member.models import HouseholdHeadEligibility, HouseholdMember, RepresentativeEligibility
from household.models.household_log import HouseholdLog
from edc_constants.constants import ALIVE, YES, MALE


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app_config = django_apps.get_app_config('enumeration')
        self.survey = context.get('survey')
        self.today = context.get('today', arrow.utcnow())  # for tests
        try:
            survey_breadcrumb = format_html(' &#9654; '.join(context.get('survey').split('.')))
        except AttributeError:
            survey_breadcrumb = None
        self.household_identifier = context.get('household_identifier')
        try:
            self.household_structure = HouseholdStructure.objects.get(
                household__household_identifier=self.household_identifier,
                survey=self.survey)
        except HouseholdStructure.DoesNotExist:
            self.household_structure = None
        self.household_log_entries = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by('-report_datetime')
        self.household_members = HouseholdMember.objects.filter(
            household_structure=self.household_structure).order_by('first_name')
        context.update(
            site_header=admin.site.site_header,
            ALIVE=ALIVE,
            YES=YES,
            MALE=MALE,
            enumeration_dashboard_base_html=app_config.enumeration_dashboard_base_html,
            navbar_selected='enumeration',
            survey_breadcrumb=survey_breadcrumb,
            can_add_members=self.can_add_members,
            household_log=HouseholdLog.objects.get(household_structure=self.household_structure),
            household_log_entries=self.household_log_entries,
            household_members=self.household_members,
            household_structure=self.household_structure,
            todays_household_log_entry=self.todays_household_log_entry,
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
    def can_add_hoh_eligibility(self):
        if self.household_members:
            return True
        return False

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
        """Return "today's" household log entry, or none."""
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
        """Returns the household member that is the Head of Household."""
        try:
            obj = HouseholdMember.objects.get(
                household_structure=self.household_structure,
                relation=HEAD_OF_HOUSEHOLD)
        except HouseholdMember.DoesNotExist:
            obj = None
        return obj

    @property
    def head_of_household_eligibility(self):
        """Return the head of household eligibility."""
        try:
            obj = HouseholdHeadEligibility.objects.get(
                household_member=self.head_of_household)
        except HouseholdHeadEligibility.DoesNotExist:
            obj = None
        return obj

    @property
    def representative_eligibility(self):
        """Return the representative eligibility."""
        try:
            obj = RepresentativeEligibility.objects.get(
                household_structure=self.household_structure)
        except RepresentativeEligibility.DoesNotExist:
            obj = None
        return obj
