from edc_base.utils import get_utcnow
from edc_dashboard.listboard_filter import ListboardFilter, ListboardViewFilters


class HouseholdStructureListboardViewFilters(ListboardViewFilters):

    all = ListboardFilter(
        name='all',
        position=0,
        label='All',
        lookup={})

    enrolled = ListboardFilter(
        label='Enrolled',
        position=10,
        lookup={'enrolled': True})

    enrolled_today = ListboardFilter(
        label='Enrolled today',
        position=11,
        lookup={
            'enrolled': True,
            'enrolled_datetime__date__gte': get_utcnow().date()})

    not_enrolled = ListboardFilter(
        label='Not enrolled',
        position=20,
        lookup={'enrolled': False})

    enumerated = ListboardFilter(
        label='Enumerated',
        position=30,
        lookup={'enumerated': True})

    enumerated_today = ListboardFilter(
        label='Enumerated today',
        position=31,
        lookup={
            'enumerated': True,
            'enumerated_datetime__date__gte': get_utcnow().date()})

    not_enumerated = ListboardFilter(
        label='Not enumerated',
        position=40,
        lookup={'enumerated': False})

    refused_enumeration = ListboardFilter(
        label='Refused Enumeration',
        position=50,
        lookup={'refused_enumeration': True})

    no_informant = ListboardFilter(
        label='No informant',
        position=60,
        lookup={'no_informant': True})
