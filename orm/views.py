from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import *
from orm.models import *
import datetime
import pytz
from dateutil import parser


# Create your views here.
def submissions(request):
    params = request.GET
    try:
        page = int(params.get('page', 1))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    try:
        per_page = int(params.get('per_page', 10))
    except ValueError:
        per_page = 10
    if per_page < 1:
        per_page = 10

    page_num = (page - 1) * per_page

    order_type = params.get('order_type', 'desc').lower()
    if order_type == 'desc':
        order_type = '-'
    else:
        order_type = ''

    order_params = params.get('order_by', '?').replace(' ', '').lower().split(',')
    order_list = []

    for column in order_params:
        if column in ('id', 'br_court_name', 'kind_name', 'cin', 'registration_date', 'corporate_body_name',
                            'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city'):
            order_list.append(order_type + column)

    gte = ''
    lte = ''
    if 'registration_date_gte' in params:
        try:
            dt = parser.parse(params['registration_date_gte'])
            gte = datetime.date(year=dt.year, month=dt.month, day=dt.day)
        except ValueError:
            gte = ''
    if 'registration_date_lte' in params:
        try:
            dt = parser.parse(params['registration_date_lte'])
            lte = datetime.date(year=dt.year, month=dt.month, day=dt.day)
        except ValueError:
            lte = ''

    total = OrPodanieIssues.objects.filter(Q(corporate_body_name__contains=params['query']) |
                                           Q(city__contains=params['query']),
                                           registration_date__lte=lte,
                                           registration_date__gte=gte).count()
    result = OrPodanieIssues.objects.filter(Q(corporate_body_name__contains=params['query']) |
                                            Q(city__contains=params['query']),
                                            registration_date__lte=lte,
                                            registration_date__gte=gte).order_by(*order_list)[page_num:(page_num + per_page)]

    response = {'items': []}
    pages_count = total // per_page
    if total % per_page != 0:
        pages_count += 1

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': pages_count, 'total': total}

    for row in result:
        entry = {'id': row.id, 'br_court_name': row.br_court_name, 'kind_name': row.kind_name, 'cin': row.cin.cin,
                 'registration_date': str(row.registration_date), 'corporate_body_name': row.corporate_body_name,
                 'br_section': row.br_section, 'br_insertion': row.br_insertion, 'text': row.text, 'street': row.street,
                 'postal_code': row.postal_code, 'city': row.city}
        response['items'].append(entry)

    return JsonResponse(response)


def companies(request):
    params = request.GET
    result = Companies.objects.filter(cin=params['cin'])
    response = {'items': []}
    for row in result:
        entry = {'cin': row.cin, 'name': row.name, 'br_section': row.br_section, 'address_line': row.address_line,
                 'last_update': str(row.last_update), 'or_podanie_issues_count': row.or_podanie_issues_count,
                 'znizenie_imania_issues_count': row[6], 'likvidator_issues_count': row[7],
                 'konkurz_vyrovnanie_issues_count': row[8], 'konkurz_restrukturalizacia_actors_count': row[9]}
        response['items'].append(entry)
    return JsonResponse(response)
