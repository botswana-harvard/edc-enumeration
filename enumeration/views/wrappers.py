from uuid import uuid4

from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist

from edc_base.utils import get_utcnow
from edc_consent.exceptions import ConsentDoesNotExist
from edc_consent.site_consents import site_consents

from bcpp_subject.views.dashboard.default.wrappers import (
    SubjectConsentModelWrapper as BaseSubjectConsentModelWrapper)
from bcpp_subject.models import SubjectConsent
from household.exceptions import HouseholdLogRequired
from household.views import (
    HouseholdStructureWithLogEntryWrapper as BaseHouseholdStructureWithLogEntryWrapper,
    HouseholdLogEntryModelWrapper as BaseHouseholdLogEntryModelWrapper)
from member.models.household_member.utils import (
    is_minor, is_adult, todays_log_entry_or_raise)
from member.views.wrappers import (
    HouseholdMemberModelWrapper as BaseHouseholdMemberModelWrapper,
    RepresentativeEligibilityModelWrapper as BaseRepresentativeEligibilityModelWrapper,
    HouseholdInfoModelWrapper as BaseHouseholdInfoModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper as BaseHeadOfHouseholdEligibilityModelWrapper,
)


class HeadOfHouseholdEligibilityModelWrapper(
        BaseHeadOfHouseholdEligibilityModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class HouseholdInfoModelWrapper(BaseHouseholdInfoModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class RepresentativeEligibilityModelWrapper(
        BaseRepresentativeEligibilityModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class HouseholdLogEntryModelWrapper(BaseHouseholdLogEntryModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class SubjectConsentModelWrapper(BaseSubjectConsentModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class HouseholdMemberModelWrapper(BaseHouseholdMemberModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name
    consent_model_wrapper_class = SubjectConsentModelWrapper

    @property
    def editable_in_view(self):
        """Returns True if object and its related objects can be
        edited in the dashboard view.

        See dashboard_view.get().
        """
        return self._original_object.editable_in_view

    @property
    def participation_status(self):
        return self._original_object.participation_status

    @property
    def is_clone_not_updated(self):
        if (self._original_object.cloned
                and not self._original_object.clone_updated):
            return True
        return False

    @property
    def is_consented(self):
        return self._original_object.is_consented

    @property
    def consent(self):
        """Returns a wrapped saved or unsaved consent.
        """
        consent = None
        if self._original_object:
            if self._original_object.consent:
                consent = self._original_object.consent
            else:
                consent = self._original_object.consent_object.model(
                    subject_identifier=self._original_object.subject_identifier,
                    consent_identifier=uuid4(),
                    household_member=self._original_object,
                    survey_schedule=self._original_object.survey_schedule_object.field_value,
                    version=self._original_object.consent_object.version)
            consent = self.consent_model_wrapper_class(consent)
        return consent

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

            self.is_minor = is_minor(self.wrapped_object.age_in_years)
            self.is_adult = is_adult(self.wrapped_object.age_in_years)
            if self.refused:
                self.done = True


class HouseholdStructureWithLogEntryWrapper(
        BaseHouseholdStructureWithLogEntryWrapper):

    def get_current_log_entry(self, report_datetime=None):
        for log_entry in self.log_entries.all():
            household_structure = log_entry.household_log.household_structure
            try:
                log_entry = todays_log_entry_or_raise(
                    household_structure,
                    report_datetime=report_datetime or get_utcnow())
            except HouseholdLogRequired:
                pass
            else:
                return log_entry
        return None

    @property
    def members(self):
        return self.parent._original_object.householdmember_set.all()
