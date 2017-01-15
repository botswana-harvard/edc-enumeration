from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import ALIVE, YES, MALE
from edc_dashboard.view_mixins import DashboardViewMixin, SubjectIdentifierViewMixin

from household.models import HouseholdLogEntry
from household.views import (
    HouseholdViewMixin, HouseholdStructureViewMixin,
    HouseholdLogEntryViewMixin)
from member.constants import HEAD_OF_HOUSEHOLD
from member.models import (
    HouseholdHeadEligibility, RepresentativeEligibility, HouseholdInfo)
from member.views import HouseholdMemberViewMixin
from survey.view_mixins import SurveyViewMixin

from .mixins import EnumerationAppConfigViewMixin
from .wrappers import HouseholdMemberModelWrapper
from django.core.exceptions import ObjectDoesNotExist


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


class DashboardView(EdcBaseViewMixin, DashboardViewMixin, SubjectIdentifierViewMixin,
                    SurveyViewMixin, HouseholdViewMixin,
                    HouseholdStructureViewMixin, HouseholdLogEntryViewMixin,
                    HouseholdMemberViewMixin, EnumerationAppConfigViewMixin, TemplateView):

    app_config_name = 'enumeration'
    household_member_wrapper_class = HouseholdMemberModelWrapper

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.today = context.get('today')  # for tests
        context.update(
            ALIVE=ALIVE,
            YES=YES,
            MALE=MALE,
            can_add_members=self.can_add_members,
            eligibility_buttons=self.eligibility_buttons(self.household_structure),
            alert=self.alert,
        )
        return context

    @property
    def alert(self):
        if not self.current_household_log_entry:
            return 'Please complete a {} for today.'.format(
                HouseholdLogEntry._meta.verbose_name)
        elif not self.representative_eligibility:
            return 'Please complete the {} form.'.format(
                RepresentativeEligibility._meta.verbose_name)
        elif not self.household_info:
            return 'Please complete the {} form.'.format(
                HouseholdInfo._meta.verbose_name)
        elif not self.head_of_household_eligibility and self.head_of_household:
            return 'Please complete the {} form.'.format(
                HouseholdHeadEligibility._meta.verbose_name)
        else:
            return None

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
            household_info = HouseholdInfo.objects.get(
                household_structure__id=self.household_structure.id)
        except HouseholdInfo.DoesNotExist:
            household_info = HouseholdInfo()
        if not self.representative_eligibility:
            btn.disabled = True
        if not self.current_household_log_entry and btn.add:
            btn.disabled = True
        btn = Button(household_info, household_structure=household_structure.wrapped_object)
        eligibility_buttons.append(btn)
        return eligibility_buttons

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
            obj = self.household_structure.wrapped_object.representativeeligibility
        except ObjectDoesNotExist:
            obj = None
        return obj

    @property
    def household_info(self):
        """Return the household_info model instance."""
        try:
            obj = self.household_structure.wrapped_object.householdinfo
        except ObjectDoesNotExist:
            obj = None
        return obj
