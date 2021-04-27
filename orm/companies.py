from django.http import JsonResponse
from django.db.models import *
from orm.models import *
import datetime
import pytz
from dateutil import parser


def get(request):
    params = request.GET
    result = Companies.objects.filter(cin=params['cin'])\
        .annotate(or_podanie_issues_count=Count('orpodanieissues'))\
        .annotate(znizenie_imania_issues_count=Count('znizenieimaniaissues'))\
        .annotate(likvidator_issues_count=Count('likvidatorissues'))\
        .annotate(konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues'))\
        .annotate(konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors'))
    response = {'items': []}
    for row in result:
        entry = {'cin': row.cin, 'name': row.name, 'br_section': row.br_section, 'address_line': row.address_line,
                 'last_update': str(row.last_update), 'or_podanie_issues_count': row.or_podanie_issues_count,
                 'znizenie_imania_issues_count': row.znizenie_imania_issues_count,
                 'likvidator_issues_count': row.likvidator_issues_count,
                 'konkurz_vyrovnanie_issues_count': row.konkurz_vyrovnanie_issues_count,
                 'konkurz_restrukturalizacia_actors_count': row.konkurz_restrukturalizacia_actors_count}
        response['items'].append(entry)
    return JsonResponse(response)