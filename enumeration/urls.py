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
from django.conf.urls import url

from edc_constants.constants import UUID_PATTERN

from household.patterns import household_identifier
from plot.patterns import plot_identifier
from survey.patterns import survey

from .views import EnumerationView, EnumerationDashboardView

urlpatterns = [
    url(r'^dashboard/(?P<household_identifier>' + household_identifier + ')/(?P<survey>' + survey + ')/',
        EnumerationDashboardView.as_view(), name='dashboard_url'),
    url(r'^list/(?P<page>\d+)/', EnumerationDashboardView.as_view(), name='list_url'),
    url(r'^list/(?P<plot_identifier>' + plot_identifier + ')/', EnumerationView.as_view(), name='list_url'),
    url(r'^list/(?P<household_identifier>' + household_identifier + ')/(?P<survey>' + survey + ')/',
        EnumerationView.as_view(), name='list_url'),
    url(r'^list/(?P<household_identifier>' + household_identifier + ')/',
        EnumerationView.as_view(), name='list_url'),
    url(r'^list/(?P<id>' + UUID_PATTERN.pattern + ')/', EnumerationView.as_view(), name='list_url'),
    url(r'^list/', EnumerationView.as_view(), name='list_url'),
]
