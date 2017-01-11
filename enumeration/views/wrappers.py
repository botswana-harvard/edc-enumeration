from household.views.wrappers import (
    HouseholdStructureWithLogEntryWrapper as HouseholdStructureWithLogEntryWrapperParent)


class HouseholdStructureWithLogEntryWrapper(HouseholdStructureWithLogEntryWrapperParent):

    @property
    def members(self):
        return self.parent._original_object.householdmember_set.all()
