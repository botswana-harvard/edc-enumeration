from uuid import uuid4

from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist

from edc_base.utils import get_utcnow
from edc_consent.site_consents import site_consents
from edc_consent.exceptions import ConsentDoesNotExist

from bcpp_subject.views.dashboard.default.wrappers import (
    SubjectConsentModelWrapper as BaseSubjectConsentModelWrapper)
from bcpp_subject.models import SubjectConsent
from household.exceptions import HouseholdLogRequired
from household.views import (
    HouseholdStructureWithLogEntryWrapper as BaseHouseholdStructureWithLogEntryWrapper,
    HouseholdLogEntryModelWrapper as BaseHouseholdLogEntryModelWrapper)
from member.constants import AVAILABLE
from member.models.household_member.utils import is_minor, is_adult, todays_log_entry_or_raise
from member.participation_status import ParticipationStatus
from member.views.wrappers import (
    HouseholdMemberModelWrapper as BaseHouseholdMemberModelWrapper,
    RepresentativeEligibilityModelWrapper as BaseRepresentativeEligibilityModelWrapper,
    HouseholdInfoModelWrapper as BaseHouseholdInfoModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper as BaseHeadOfHouseholdEligibilityModelWrapper,
)


class HeadOfHouseholdEligibilityModelWrapper(BaseHeadOfHouseholdEligibilityModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class HouseholdInfoModelWrapper(BaseHouseholdInfoModelWrapper):

    next_url_name = django_apps.get_app_config(
        'enumeration').dashboard_url_name


class RepresentativeEligibilityModelWrapper(BaseRepresentativeEligibilityModelWrapper):

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
    consent_model = SubjectConsent

    @property
    def consent_object(self):
        """Returns a consent object or None from site_consents
        for the current period."""
        try:
            return site_consents.get_consent(
                report_datetime=self._original_object.report_datetime)
        except ConsentDoesNotExist:
            return None

    @property
    def consent(self):
        """Returns a wrapped saved or unsaved consent or None."""
        try:
            consent = self._original_object.subjectconsent_set.get(
                version=self.consent_object.version)
        except ObjectDoesNotExist:
            if self.consent_object:
                consent = self.consent_model(
                    subject_identifier=self._original_object.subject_identifier,
                    consent_identifier=uuid4(),
                    household_member=self._original_object,
                    survey_schedule=self._original_object.survey_schedule_object.field_value,
                    version=self.consent_object.version)
            else:
                consent = None
        if consent:
            consent = self.consent_model_wrapper_class(consent)
        return consent

    def add_extra_attributes_after(self):
        super().add_extra_attributes_after()
        if self.wrapped_object.id:
            self.refused = self.wrapped_object.refused
            try:
                # FIXME: ANONYMOUS
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
