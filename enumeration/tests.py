from django.test import TestCase, tag

from member.tests.test_mixins import MemberMixin
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from django.urls.base import reverse

from household.models.household_log_entry import HouseholdLogEntry

from .views import DashboardView
from dateutil.relativedelta import relativedelta


class TestEnumeration(MemberMixin, TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='erik')
        self.household_structure = self.make_household_ready_for_enumeration(make_hoh=False)

    def test_dashboard_view(self):
        url = reverse('dashboard_url', kwargs=dict(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey))
        request = self.factory.get(url)
        request.user = self.user
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_todays_household_log_entry_is_none(self):
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey)

    def test_todays_household_log_entry_is_not_none(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey,
            today=household_log_entry.report_datetime)
        self.assertIsNotNone(view.todays_household_log_entry)

    def test_can_add_members_if_log_entry_today(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey,
            today=household_log_entry.report_datetime)
        self.assertTrue(view.can_add_members)

    def test_does_not_can_add_members_if_no_log_entry_today(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey,
            today=household_log_entry.report_datetime + relativedelta(days=3))
        self.assertFalse(view.can_add_members)

    def test_enable_head_of_household_eligibility(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey=self.household_structure.survey,
            today=household_log_entry.report_datetime + relativedelta(days=3))
        self.assertFalse(view.disable_hoh_eligibility)
