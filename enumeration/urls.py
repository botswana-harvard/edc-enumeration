"""household URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import sys

from django.conf.urls import url

from edc_constants.constants import UUID_PATTERN

from household.patterns import household_identifier
from plot.patterns import plot_identifier
from survey.patterns import survey_schedule

from .views import ListBoardView, DashboardView, CloneMembersView


urlpatterns = [
    url(r'^dashboard/'
        '(?P<subject_identifier>' + '[0-9]{3}\-[0-9\-]+' + ')/'
        '(?P<household_identifier>' + household_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        DashboardView.as_view(), name='dashboard_url'),
    url(r'^dashboard/'
        '(?P<subject_identifier>' + UUID_PATTERN.pattern + ')/'
        '(?P<household_identifier>' + household_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        DashboardView.as_view(), name='dashboard_url'),
    url(r'^dashboard/'
        '(?P<household_identifier>' + household_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        DashboardView.as_view(), name='dashboard_url'),
    url(r'^dashboard/import_members/'
        '(?P<household_identifier>' + household_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        CloneMembersView.as_view(), name='dashboard_import_members_url'),
    url(r'^listboard/'
        '(?P<household_identifier>' + household_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<household_identifier>' + household_identifier + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<plot_identifier>' + plot_identifier + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<plot_identifier>' + plot_identifier + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<household_structure>' + UUID_PATTERN.pattern + ')/'
        '(?P<survey_schedule>' + survey_schedule + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<household_structure>' + UUID_PATTERN.pattern + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/(?P<page>[0-9]+)/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/'
        '(?P<id>' + UUID_PATTERN.pattern + ')/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'^listboard/',
        ListBoardView.as_view(), name='listboard_url'),
    url(r'', ListBoardView.as_view(), name='home_url'),
]

if 'test' in sys.argv:
    from django.conf.urls import include
    from django.contrib import admin
    from edc_base.views import LoginView, LogoutView
    urlpatterns += [
        url(r'^admin/', admin.site.urls),
        url(r'^edc/', include('edc_base.urls', 'edc-base')),
        url(r'^tz_detect/', include('tz_detect.urls')),
        url(r'login', LoginView.as_view(), name='login_url'),
        url(r'logout', LogoutView.as_view(
            pattern_name='login_url'), name='logout_url'),
    ]
