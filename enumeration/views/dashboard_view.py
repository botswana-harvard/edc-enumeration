from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import ALIVE, YES, MALE
from edc_dashboard.view_mixins import DashboardViewMixin, SubjectIdentifierViewMixin, AppConfigViewMixin

from household.models import HouseholdLogEntry
from household.views import (
    HouseholdViewMixin, HouseholdStructureViewMixin,
    HouseholdLogEntryViewMixin)
from member.models import (
    HouseholdHeadEligibility, RepresentativeEligibility, HouseholdInfo)
from member.views import (
    HouseholdMemberViewMixin, RepresentativeEligibilityModelWrapper,
    HeadOfHouseholdEligibilityModelWrapper, HouseholdInfoModelWrapper)
from survey.view_mixins import SurveyViewMixin

from .wrappers import HouseholdMemberModelWrapper, HouseholdLogEntryModelWrapper


class DashboardView(EdcBaseViewMixin, DashboardViewMixin, AppConfigViewMixin,
                    SubjectIdentifierViewMixin,
                    SurveyViewMixin, HouseholdViewMixin,
                    HouseholdStructureViewMixin, HouseholdLogEntryViewMixin,
                    HouseholdMemberViewMixin, TemplateView):

    app_config_name = 'enumeration'
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
            eligibility_wrapped_models=self.eligibility_wrapped_models,
            alert_danger=None if not self.alert_danger else mark_safe(self.alert_danger),
            # alert_success='Thanks',
        )
        return context

    @property
    def alert_danger(self):
        if not self.current_household_log_entry.id:
            return 'Please complete a <a href="{url}" class="alert-link">{form}</a> for today.'.format(
                form=HouseholdLogEntry._meta.verbose_name,
                url=HouseholdLogEntry().get_absolute_url())
        elif not self.representative_eligibility:
            return 'Please complete the <a href="{url}" class="alert-link">{form}</a> form.'.format(
                form=RepresentativeEligibility._meta.verbose_name,
                url=RepresentativeEligibility().get_absolute_url())
        elif not self.household_info:
            return 'Please complete the <a href="{url}" class="alert-link">{form}</a>  form.'.format(
                form=HouseholdInfo._meta.verbose_name,
                url=HouseholdInfo().get_absolute_url())
        elif not self.head_of_household_eligibility and self.head_of_household:
            return 'Please complete the <a href="{url}" class="alert-link">{form}</a> form.'.format(
                form=HouseholdHeadEligibility._meta.verbose_name,
                url=HouseholdHeadEligibility().get_absolute_url())
        else:
            return None

    @property
    def can_add_members(self):
        """Returns True if the user will be allowed to add new members."""
        if not self.representative_eligibility or not self.current_household_log_entry:
            return False
        return True

    @property
    def eligibility_wrapped_models(self):

        eligibility_wrapped_models = []

        # representative_eligibility  # FIXME: not wrapped!!
        if self.representative_eligibility:
            wrapped = RepresentativeEligibilityModelWrapper(
                self.representative_eligibility,
                model_name=RepresentativeEligibility._meta.label_lower,
                next_url_name=self.dashboard_url_name)
        else:
            wrapped = RepresentativeEligibilityModelWrapper(
                RepresentativeEligibility(
                    household_structure=self.household_structure._original_object),
                model_name=RepresentativeEligibility._meta.label_lower,
                next_url_name=self.dashboard_url_name)
            # can edit anytime, but can only add if have todays log...
            if not self.current_household_log_entry:
                wrapped.disabled = True
        eligibility_wrapped_models.append(wrapped)

        # head_of_household_eligibility
        if self.head_of_household.id:
            if self.head_of_household_eligibility:
                wrapped = HeadOfHouseholdEligibilityModelWrapper(
                    self.head_of_household_eligibility,
                    model_name=HouseholdHeadEligibility._meta.label_lower,
                    next_url_name=self.dashboard_url_name)
            else:
                wrapped = HeadOfHouseholdEligibilityModelWrapper(
                    HouseholdHeadEligibility(
                        household_member=self.head_of_household._original_object),
                    model_name=HouseholdHeadEligibility._meta.label_lower,
                    next_url_name=self.dashboard_url_name)
                # can edit anytime, but can only add if have todays log...
                if not self.current_household_log_entry:
                    wrapped.disabled = True
        eligibility_wrapped_models.append(wrapped)

        # household_info  # FIXME: not wrapped!!
        if self.household_info:
            wrapped = HouseholdInfoModelWrapper(
                self.household_info,
                model_name=HouseholdInfo._meta.label_lower,
                next_url_name=self.dashboard_url_name)
        else:
            wrapped = HouseholdInfoModelWrapper(
                HouseholdInfo(
                    household_structure=self.household_structure._original_object),
                model_name=HouseholdInfo._meta.label_lower,
                next_url_name=self.dashboard_url_name)
            # can edit anytime, but can only add if have todays log...
            if not self.current_household_log_entry:
                wrapped.disabled = True
        eligibility_wrapped_models.append(wrapped)
        return eligibility_wrapped_models

    @property
    def head_of_household_eligibility(self):  # FIXME: should be wrapped!!
        """Return the head of household eligibility model instance or None."""
        try:
            obj = HouseholdHeadEligibility.objects.get(
                household_member=self.head_of_household._original_object)
        except HouseholdHeadEligibility.DoesNotExist:
            obj = None
        return obj

    @property
    def representative_eligibility(self):   # FIXME: should be wrapped!!
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
