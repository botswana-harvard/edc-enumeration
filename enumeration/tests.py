from dateutil.relativedelta import relativedelta

from django.test import TestCase, tag
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.urls.base import reverse

from household.models.household_log_entry import HouseholdLogEntry
from member.tests import MemberTestMixin

from .views import DashboardView
from household.tests.household_test_mixin import HouseholdTestMixin
from edc_base_test.mixins.dates_test_mixin import DatesTestMixin
from survey.tests.dates_test_mixin import DatesTestMixin as SurveyDatesTestMixin
from plot.tests.plot_test_mixin import PlotTestMixin


class TestEnumeration(MemberTestMixin, TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='erik')
        self.household_structure = self.make_household_ready_for_enumeration(make_hoh=False)

#     def test_queryset_wrapper(self):
#         view = ListBoardView()
#         results = view.paginate([self.household_structure], view.filtered_model_wrapper_class)
#         self.assertEqual(
#             results[0].plot_identifier, self.household_structure.household.plot.plot_identifier)
#         self.assertEqual(
#             results[0].household_identifier, self.household_structure.household.household_identifier)
#         self.assertEqual(results[0].members.count(), 0)
#         self.assertEqual(results[0].community_name, 'test community')
#         self.assertEqual(results[0].survey_schedule_name, 'annual')
#         self.assertEqual(results[0].survey_schedule_year, 'example-survey_schedule-3')
#         household_structure = self.make_household_ready_for_enumeration(make_hoh=True)
#         results = view.queryset_wrapper([household_structure])
#         self.assertGreater(results[0].members.count(), 0)


class TestDashboard(MemberTestMixin, HouseholdTestMixin, PlotTestMixin,
                    SurveyDatesTestMixin, DatesTestMixin, TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='erik')
        self.household_structure = self.make_household_ready_for_enumeration(make_hoh=False)

    def test_dashboard_view(self):
        url = reverse('dashboard_url', kwargs=dict(
            household_identifier=self.household_structure.household.household_identifier,
            survey_schedule=self.household_structure.survey_schedule))
        request = self.factory.get(url)
        request.user = self.user
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_current_household_log_entry_is_none(self):
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey_schedule=self.household_structure.survey_schedule)

    def test_current_household_log_entry_is_not_none(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey_schedule=self.household_structure.survey_schedule,
            today=household_log_entry.report_datetime)
        self.assertIsNotNone(view.current_household_log_entry)

    def test_can_add_members_if_log_entry_today(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey_schedule=self.household_structure.survey_schedule,
            today=household_log_entry.report_datetime)
        self.assertTrue(view.can_add_members)

    def test_can_not_add_members_if_no_log_entry_today(self):
        household_log_entry = HouseholdLogEntry.objects.filter(
            household_log__household_structure=self.household_structure).order_by(
                'report_datetime').last()
        view = DashboardView()
        view.get_context_data(
            household_identifier=self.household_structure.household.household_identifier,
            survey_schedule=self.household_structure.survey_schedule,
            today=household_log_entry.report_datetime + relativedelta(days=3))
        self.assertFalse(view.can_add_members)
