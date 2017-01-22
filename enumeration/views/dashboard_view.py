from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

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


class DashboardView(EdcBaseViewMixin, DashboardViewMixin, AppConfigViewMixin,
                    SubjectIdentifierViewMixin,
                    SurveyViewMixin, HouseholdViewMixin,
                    HouseholdStructureViewMixin, HouseholdLogEntryViewMixin,
                    HouseholdMemberViewMixin, TemplateView):

    app_config_name = 'enumeration'
    navbar_item_selected = 'enumeration'
    household_member_wrapper_class = HouseholdMemberModelWrapper
    household_log_entry_wrapper_class = HouseholdLogEntryModelWrapper

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
            household_forms=self.household_forms_as_wrapped_models,
            alert_danger=None if not self.alert_danger else mark_safe(self.alert_danger),
            # alert_success='Thanks',
        )
        return context

    @property
    def alert_danger(self):
        if not self.current_household_log_entry:
            return ('Please complete a <a href="{href}" class="alert-link">{form}</a> '
                    'for today before adding any new data.').format(
                        form=HouseholdLogEntry._meta.verbose_name,
                        href=self.current_household_log_entry.href)
        elif not self.representative_eligibility:
            return 'Please complete the <a href="{href}" class="alert-link">{form}</a> form.'.format(
                form=RepresentativeEligibility._meta.verbose_name,
                href=self.representative_eligibility.href)
        elif not self.household_info:
            return 'Please complete the <a href="{href}" class="alert-link">{form}</a>  form.'.format(
                form=HouseholdInfo._meta.verbose_name,
                href=self.household_info.href)
        elif not self.head_of_household_eligibility and self.head_of_household:
            return 'Please complete the <a href="{href}" class="alert-link">{form}</a> form.'.format(
                form=HouseholdHeadEligibility._meta.verbose_name,
                href=self.head_of_household_eligibility.href)
        else:
            return None

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new members."""
        if not self.representative_eligibility or not self.current_household_log_entry:
            return False
        return True

    @property
    def household_forms_as_wrapped_models(self):
        """Returns a generator of "Household forms" to be completed
        prior to enumeration."""
        wrapped_models = (
            self.representative_eligibility,
            self.household_info,
            self.head_of_household_eligibility)
        for wrapped_model in wrapped_models:
            if wrapped_model is not None:
                if not self.current_household_log_entry:
                    wrapped_model.disabled = True
                yield wrapped_model
            else:
                continue

    @property
    def head_of_household_eligibility(self):
        """Return a wrapped model saved/unsaved if HoH exists, otherwise None."""
        if self.head_of_household:
            try:
                obj = HouseholdHeadEligibility.objects.get(
                    household_member=self.head_of_household._original_object)
            except ObjectDoesNotExist:
                obj = HouseholdHeadEligibility(
                    household_member=self.head_of_household._original_object)
            return HeadOfHouseholdEligibilityModelWrapper(
                obj, model_name=HouseholdHeadEligibility._meta.label_lower,
                next_url_name=self.dashboard_url_name)
        return None

    @property
    def representative_eligibility(self):
        """Return a wrapped model of either saved or unsaved."""
        try:
            obj = self.household_structure._original_object.representativeeligibility
        except ObjectDoesNotExist:
            obj = RepresentativeEligibility(
                household_structure=self.household_structure._original_object)
        return RepresentativeEligibilityModelWrapper(
            obj, model_name=RepresentativeEligibility._meta.label_lower,
            next_url_name=self.dashboard_url_name)

    @property
    def household_info(self):
        """Return a wrapped model of either saved or unsaved."""
        try:
            obj = self.household_structure._original_object.householdinfo
        except ObjectDoesNotExist:
            obj = HouseholdInfo(
                household_structure=self.household_structure._original_object)
        return HouseholdInfoModelWrapper(
            obj, model_name=HouseholdInfo._meta.label_lower,
            next_url_name=self.dashboard_url_name)
