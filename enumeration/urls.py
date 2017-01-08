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
from survey.patterns import survey

from .views import ListView, DashboardView


urlpatterns = [
    url(r'^dashboard/(?P<household_identifier>' + household_identifier + ')/(?P<survey>' + survey + ')/',
        DashboardView.as_view(), name='dashboard_url'),
    url(r'^dashboard/(?P<household_member>' + UUID_PATTERN.pattern + ')/',
        DashboardView.as_view(), name='dashboard_url'),
    url(r'^list/(?P<page>[0-9]+)/', ListView.as_view(), name='list_url'),
    url(r'^list/(?P<household_identifier>' + household_identifier + ')/(?P<survey>' + survey + ')/',
        ListView.as_view(), name='list_url'),
    url(r'^list/(?P<plot_identifier>' + plot_identifier + ')/(?P<survey>' + survey + ')',
        ListView.as_view(), name='list_url'),
    url(r'^list/(?P<plot_identifier>' + plot_identifier + ')/', ListView.as_view(), name='list_url'),
    url(r'^list/(?P<household_identifier>' + household_identifier + ')/',
        ListView.as_view(), name='list_url'),
    url(r'^list/(?P<household_structure>' + UUID_PATTERN.pattern + ')/',
        ListView.as_view(), name='list_url'),
    url(r'^list/(?P<id>' + UUID_PATTERN.pattern + ')/', ListView.as_view(), name='list_url'),
    url(r'^list/', ListView.as_view(), name='list_url'),
    url(r'', ListView.as_view(), name='home_url'),
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
        url(r'logout', LogoutView.as_view(pattern_name='login_url'), name='logout_url'),
    ]
