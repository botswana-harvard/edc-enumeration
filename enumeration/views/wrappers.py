from household.views.wrappers import (
    HouseholdStructureWithLogEntryWrapper as BaseHouseholdStructureWithLogEntryWrapper)

from member.constants import AVAILABLE
from member.models.household_member.utils import is_minor, is_adult
from member.participation_status import ParticipationStatus
from member.views.wrappers import HouseholdMemberModelWrapper as BaseHouseholdMemberModelWrapper
from django.core.exceptions import ObjectDoesNotExist


class HouseholdStructureWithLogEntryWrapper(BaseHouseholdStructureWithLogEntryWrapper):

    @property
    def members(self):
        return self.parent._original_object.householdmember_set.all()


class HouseholdMemberModelWrapper(BaseHouseholdMemberModelWrapper):

    def add_from_wrapped_model(self):
        super().add_from_wrapped_model()
        self.verbose_name = self.wrapped_object.verbose_name
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
