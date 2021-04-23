from django.http import JsonResponse
from django.db.models import *
from orm.models import *
import datetime
import pytz
from dateutil import parser


def get(request):
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