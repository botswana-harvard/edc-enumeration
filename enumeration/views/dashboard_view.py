from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.contrib import messages
from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import ALIVE, DEAD, YES, MALE, NO, NOT_APPLICABLE
from edc_dashboard.view_mixins import DashboardViewMixin
from edc_dashboard.view_mixins import SubjectIdentifierViewMixin, AppConfigViewMixin
from household_dashboard.view_mixins import HouseholdLogEntryViewMixin
from household_dashboard.view_mixins import HouseholdStructureViewMixin
from household_dashboard.view_mixins import HouseholdViewMixin
from member.constants import HEAD_OF_HOUSEHOLD
from member_dashboard.view_mixins import HouseholdMemberViewMixin
from survey.view_mixins import SurveyViewMixin

from ..model_wrappers import (
    HouseholdMemberModelWrapper, HouseholdLogEntryModelWrapper,
    RepresentativeEligibilityModelWrapper, HouseholdInfoModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper, HouseholdAssessmentModelWrapper)
from household.constants import NO_HOUSEHOLD_INFORMANT


class DashboardView(HouseholdMemberViewMixin,
                    HouseholdLogEntryViewMixin,
                    HouseholdStructureViewMixin,
                    HouseholdViewMixin,
                    SurveyViewMixin,
                    SubjectIdentifierViewMixin,
                    AppConfigViewMixin,
                    DashboardViewMixin,
                    EdcBaseViewMixin, TemplateView):

    app_config_name = 'enumeration'
    navbar_item_selected = 'enumeration'
    household_log_entry_model = 'household.householdlogentry'
    household_head_eligibility_model = 'member.householdheadeligibility'
    household_info_model = 'member.householdinfo'
    representative_eligibility_model = 'member.representativeeligibility'
    household_assessment_model = 'household.householdassessment'
    household_member_model_wrapper_cls = HouseholdMemberModelWrapper
    household_log_entry_model_wrapper_cls = HouseholdLogEntryModelWrapper

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @property
    def household_log_entry_model_cls(self):
        return django_apps.get_model(self.household_log_entry_model)

    @property
    def household_head_eligibility_model_cls(self):
        return django_apps.get_model(self.household_head_eligibility_model)

    @property
    def household_info_model_cls(self):
        return django_apps.get_model(self.household_info_model)

    @property
    def representative_eligibility_model_cls(self):
        return django_apps.get_model(self.representative_eligibility_model)

    @property
    def household_assessment_model_cls(self):
        return django_apps.get_model(self.household_assessment_model)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.today = context.get('today')  # for tests
        self.update_messages()
        context.update(
            ALIVE=ALIVE,
            DEAD=DEAD,
            YES=YES,
            NO=NO,
            MALE=MALE,
            NOT_APPLICABLE=NOT_APPLICABLE,
            HEAD_OF_HOUSEHOLD=HEAD_OF_HOUSEHOLD,
            can_add_members=self.can_add_members,
            household_forms=self.household_forms_wrapped,
        )
        return context

    def update_messages(self):
        if not self.current_household_log_entry:
            msg = mark_safe(
                'Please complete a <a href="{href}" class="alert-link">'
                '{form}</a> for today before adding any new data.'.format(
                    form=self.household_log_entry_model_cls._meta.verbose_name,
                    href=self.current_household_log_entry_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.representative_eligibility:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">'
                '{form}</a> form.'.format(
                    form=self.representative_eligibility_model_cls._meta.verbose_name,
                    href=self.representative_eligibility_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.household_info:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">'
                '{form}</a>  form.'.format(
                    form=self.household_info_model_cls._meta.verbose_name,
                    href=self.household_info_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.head_of_household_eligibility and self.head_of_household:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">{form}</a> form.'.format(
                    form=self.household_head_eligibility_model_cls._meta.verbose_name,
                    href=self.head_of_household_eligibility_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif self.current_household_log_entry.household_status == NO_HOUSEHOLD_INFORMANT:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">{form}</a> form.'.format(
                    form=self.household_assessment_model_cls._meta.verbose_name,
                    href=self.household_assessment_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new
        members.
        """
        if not self.representative_eligibility or not self.current_household_log_entry:
            return False
        elif self.current_household_log_entry.household_status == NO_HOUSEHOLD_INFORMANT:
            return False
        return True

    @property
    def household_forms_wrapped(self):
        """Returns a generator of "Household forms" to be completed
        prior to enumeration."""
        wrapped_models = (
            self.representative_eligibility_wrapped,
            self.household_info_wrapped,
            self.head_of_household_eligibility_wrapped)
        if self.current_household_log_entry:
            if self.current_household_log_entry.household_status == NO_HOUSEHOLD_INFORMANT:
                wrapped_models = wrapped_models + \
                    (self.household_assessment_wrapped,)
        for wrapped_model in wrapped_models:
            if wrapped_model is not None:
                if not self.current_household_log_entry:
                    wrapped_model.disabled = True
                yield wrapped_model
            else:
                continue

    @property
    def head_of_household_eligibility(self):
        """Return a model instance or None.
        """
        try:
            obj = self.household_head_eligibility_model_cls.objects.get(
                household_member=self.head_of_household)
        except ObjectDoesNotExist:
            obj = None
        return obj

    @property
    def head_of_household_eligibility_wrapped(self):
        """Return a wrapped model, either saved or unsaved, or None.

        Returns None if HoH does not exist.
        """
        wrapped = None
        if self.head_of_household:
            obj = (self.head_of_household_eligibility
                   or self.household_head_eligibility_model_cls(
                       household_member=self.head_of_household))
            wrapped = HeadOfHouseholdEligibilityModelWrapper(
                obj, model_name=self.household_head_eligibility_model,
                next_url_name=self.dashboard_url_name)
        return wrapped

    @property
    def representative_eligibility(self):
        """Return a representative_eligibility model instance or None.
        """
        try:
            obj = self.household_structure.representativeeligibility
        except ObjectDoesNotExist:
            obj = None
        except AttributeError:
            obj = None
        return obj

    @property
    def representative_eligibility_wrapped(self):
        """Return a wrapped model either saved or unsaved.
        """
        obj = self.representative_eligibility or self.representative_eligibility_model_cls(
            household_structure=self.household_structure)
        return RepresentativeEligibilityModelWrapper(
            obj, model_name=self.representative_eligibility_model,
            next_url_name=self.dashboard_url_name)

    @property
    def household_assessment(self):
        """Return a household_assessment model instance or None.
        """
        try:
            obj = self.household_structure.householdassessment
        except ObjectDoesNotExist:
            obj = None
        except AttributeError:
            obj = None
        return obj

    @property
    def household_assessment_wrapped(self):
        """Return a wrapped model either saved or unsaved.
        """
        obj = self.household_assessment or self.household_assessment_model_cls(
            household_structure=self.household_structure)
        return HouseholdAssessmentModelWrapper(
            obj, model_name=self.household_assessment_model,
            next_url_name=self.dashboard_url_name)

    @property
    def household_info(self):
        """Return a household info model instance or None.
        """
        try:
            obj = self.household_structure.householdinfo
        except ObjectDoesNotExist:
            obj = None
        except AttributeError:
            obj = None
        return obj

    @property
    def household_info_wrapped(self):
        """Return a wrapped model either saved or unsaved.
        """
        obj = self.household_info or self.household_info_model_cls(
            household_structure=self.household_structure)
        return HouseholdInfoModelWrapper(
            obj, model_name=self.household_info_model,
            next_url_name=self.dashboard_url_name)
