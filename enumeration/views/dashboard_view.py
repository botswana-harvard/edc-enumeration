from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from django.contrib import messages

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import ALIVE, YES, MALE
from edc_dashboard.view_mixins import (
    DashboardViewMixin, SubjectIdentifierViewMixin, AppConfigViewMixin)

from household.models import HouseholdLogEntry
from household.views import (
    HouseholdViewMixin, HouseholdStructureViewMixin,
    HouseholdLogEntryViewMixin)
from member.models import (
    HouseholdHeadEligibility, RepresentativeEligibility, HouseholdInfo)
from member.views import HouseholdMemberViewMixin
from survey.view_mixins import SurveyViewMixin

from .wrappers import (
    HouseholdMemberModelWrapper, HouseholdLogEntryModelWrapper,
    RepresentativeEligibilityModelWrapper, HouseholdInfoModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper)


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
    household_member_model_wrapper_class = HouseholdMemberModelWrapper
    household_log_entry_model_wrapper_class = HouseholdLogEntryModelWrapper

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.today = context.get('today')  # for tests
        self.update_messages()
        context.update(
            ALIVE=ALIVE,
            YES=YES,
            MALE=MALE,
            can_add_members=self.can_add_members,
            household_forms=self.household_forms_wrapped,
        )
        return context

    def update_messages(self):
        if not self.current_household_log_entry:
            msg = mark_safe(
                'Please complete a <a href="{href}" class="alert-link">'
                '{form}</a> for today before adding any new data.'.format(
                    form=HouseholdLogEntry._meta.verbose_name,
                    href=self.current_household_log_entry_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.representative_eligibility:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">'
                '{form}</a> form.'.format(
                    form=RepresentativeEligibility._meta.verbose_name,
                    href=self.representative_eligibility_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.household_info:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">'
                '{form}</a>  form.'.format(
                    form=HouseholdInfo._meta.verbose_name,
                    href=self.household_info_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)
        elif not self.head_of_household_eligibility and self.head_of_household:
            msg = mark_safe(
                'Please complete the <a href="{href}" class="alert-link">{form}</a> form.'.format(
                    form=HouseholdHeadEligibility._meta.verbose_name,
                    href=self.head_of_household_eligibility_wrapped.href))
            messages.add_message(self.request, messages.WARNING, msg)

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new
        members.
        """
        if not self.representative_eligibility or not self.current_household_log_entry:
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
            obj = HouseholdHeadEligibility.objects.get(
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
            obj = self.head_of_household_eligibility or HouseholdHeadEligibility(
                household_member=self.head_of_household)
            wrapped = HeadOfHouseholdEligibilityModelWrapper(
                obj, model_name=HouseholdHeadEligibility._meta.label_lower,
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
        obj = self.representative_eligibility or RepresentativeEligibility(
            household_structure=self.household_structure)
        return RepresentativeEligibilityModelWrapper(
            obj, model_name=RepresentativeEligibility._meta.label_lower,
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
        obj = self.household_info or HouseholdInfo(
            household_structure=self.household_structure)
        return HouseholdInfoModelWrapper(
            obj, model_name=HouseholdInfo._meta.label_lower,
            next_url_name=self.dashboard_url_name)
