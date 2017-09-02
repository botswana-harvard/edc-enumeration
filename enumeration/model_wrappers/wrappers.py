from bcpp_subject_dashboard.model_wrappers import (
    SubjectConsentModelWrapper as BaseSubjectConsentModelWrapper)
from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist
from edc_base.utils import get_utcnow, get_uuid
from household.exceptions import HouseholdLogRequired
from household_dashboard.model_wrappers import (
    HouseholdStructureWithLogEntryWrapper as BaseHouseholdStructureWithLogEntryWrapper,
    HouseholdLogEntryModelWrapper as BaseHouseholdLogEntryModelWrapper)
from household.utils import todays_log_entry_or_raise
from member.age_helper import AgeHelper
from member_dashboard.model_wrappers import (
    HouseholdMemberModelWrapper as BaseHouseholdMemberModelWrapper,
    RepresentativeEligibilityModelWrapper as BaseRepresentativeEligibilityModelWrapper,
    HouseholdInfoModelWrapper as BaseHouseholdInfoModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper as BaseHeadOfHouseholdEligibilityModelWrapper)


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
    consent_model_wrapper_cls = SubjectConsentModelWrapper

    @property
    def editable_in_view(self):
        """Returns True if object and its related objects can be
        edited in the dashboard view.

        See dashboard_view.get().
        """
        return self.object.editable_in_view

    @property
    def participation_status(self):
        return self.object.participation_status

    @property
    def is_clone_not_updated(self):
        if (self.object.cloned
                and not self.object.clone_updated):
            return True
        return False

    @property
    def is_consented(self):
        return self.object.is_consented

    @property
    def consent(self):
        """Returns a wrapped saved or unsaved consent.
        """
        # FIXME: self.object.consent_object should
        # return a consent object
        if self.object.consent:
            consent = self.object.consent
        else:
            try:
                model = self.object.consent_object.model
            except AttributeError:
                consent = None
            else:
                consent = model(
                    subject_identifier=self.object.subject_identifier,
                    consent_identifier=get_uuid(),
                    household_member=self.object,
                    survey_schedule=self.object.survey_schedule_object.field_value,
                    version=self.object.consent_object.version)
                consent = self.consent_model_wrapper_cls(consent)
        if consent:
            consent = self.consent_model_wrapper_cls(consent)
        return consent

    def add_extra_attributes_after(self):
        super().add_extra_attributes_after()
        if self.object.id:
            self.refused = self.object.refused
            try:
                self.dob = self.object.enrollmentchecklist.dob
            except ObjectDoesNotExist:
                self.dob = None
            self.survival_status = self.object.survival_status
            self.study_resident = self.object.study_resident
            self.get_relation_display = self.object.get_relation_display
            self.get_survival_status_display = self.object.get_survival_status_display
            age_helper = AgeHelper(
                age_in_years=self.object.age_in_years)
            self.is_minor = age_helper.is_minor
            self.is_adult = age_helper.is_adult
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
        return self.parent.object.householdmember_set.all()
