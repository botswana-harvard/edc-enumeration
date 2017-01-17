from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist

from edc_base.utils import get_utcnow

from household.exceptions import HouseholdLogRequired
from household.views import (
    HouseholdStructureWithLogEntryWrapper as BaseHouseholdStructureWithLogEntryWrapper,
    HouseholdLogEntryModelWrapper as BaseHouseholdLogEntryModelWrapper)
from member.constants import AVAILABLE
from member.models.household_member.utils import is_minor, is_adult, todays_log_entry_or_raise
from member.participation_status import ParticipationStatus
from member.views.wrappers import (
    HouseholdMemberModelWrapper as BaseHouseholdMemberModelWrapper)


class HouseholdLogEntryModelWrapper(BaseHouseholdLogEntryModelWrapper):

    next_url_name = django_apps.get_app_config('enumeration').dashboard_url_name


class HouseholdMemberModelWrapper(BaseHouseholdMemberModelWrapper):

    next_url_name = django_apps.get_app_config('enumeration').dashboard_url_name

    def add_extra_attributes_after(self):
        super().add_extra_attributes_after()
        if self.wrapped_object.id:
            self.refused = self.wrapped_object.refused
            try:
                self.dob = self.wrapped_object.enrollmentchecklist.dob
            except ObjectDoesNotExist:
                self.dob = None
            self.survival_status = self.wrapped_object.survival_status
            self.study_resident = self.wrapped_object.study_resident
            self.get_relation_display = self.wrapped_object.get_relation_display
            self.get_survival_status_display = self.wrapped_object.get_survival_status_display

            participation_status = ParticipationStatus(self.wrapped_object)
            self.participation_status = participation_status.participation_status
            self.get_participation_status_display = participation_status.get_participation_status_display()
            if self.participation_status == AVAILABLE:
                self.get_participation_status_display = None
            self.final_status_pending = participation_status.final_status_pending

            self.is_minor = is_minor(self.wrapped_object.age_in_years)
            self.is_adult = is_adult(self.wrapped_object.age_in_years)
            if self.refused:
                self.done = True


class HouseholdStructureWithLogEntryWrapper(BaseHouseholdStructureWithLogEntryWrapper):

    def get_current_log_entry(self, report_datetime=None):
        for log_entry in self.log_entries.all():
            household_structure = log_entry.household_log.household_structure
            try:
                log_entry = todays_log_entry_or_raise(
                    household_structure, report_datetime=report_datetime or get_utcnow())
            except HouseholdLogRequired:
                pass
            else:
                return log_entry
        return None

    @property
    def members(self):
        return self.parent._original_object.householdmember_set.all()
