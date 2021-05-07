from django.http import JsonResponse
from django.db.models import *
from orm.models import *
import datetime
import pytz
from dateutil import parser


def get(request):
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

    order_type = params.get('order_type', 'asc').lower()
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
    if 'last_update_gte' in params:
        try:
            gte = parser.parse(params['last_update_gte'])
        except ValueError:
            gte = ''

    if 'last_update_lte' in params:
        try:
            lte = parser.parse(params['last_update_lte'])
        except ValueError:
            lte = ''

    if 'query' in params:
        if lte != '' and gte != '':
            total = Companies.objects.filter(Q(name__contains=params['query']) |
                                             Q(address_line__contains=params['query']),
                                             last_update__lte=lte,
                                             last_update__gte=gte).count()
            result = Companies.objects.filter(Q(name__contains=params['query']) |
                                              Q(address_line__contains=params['query']),
                                              last_update__lte=lte,
                                              last_update__gte=gte) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        elif lte == '' and gte != '':
            total = Companies.objects.filter(Q(name__contains=params['query']) |
                                             Q(address_line__contains=params['query']),
                                             last_update__gte=gte).count()
            result = Companies.objects.filter(Q(name__contains=params['query']) |
                                              Q(address_line__contains=params['query']),
                                              last_update__gte=gte) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        elif lte != '' and gte == '':
            total = Companies.objects.filter(Q(name__contains=params['query']) |
                                             Q(address_line__contains=params['query']),
                                             last_update__lte=lte).count()
            result = Companies.objects.filter(Q(name__contains=params['query']) |
                                              Q(address_line__contains=params['query']),
                                              last_update__lte=lte) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        else:
            total = Companies.objects.filter(Q(name__contains=params['query']) |
                                             Q(address_line__contains=params['query'])).count()
            result = Companies.objects.filter(Q(name__contains=params['query']) |
                                              Q(address_line__contains=params['query'])) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
    else:
        if lte != '' and gte != '':
            total = Companies.objects.filter(last_update__lte=lte,
                                             last_update__gte=gte).count()
            result = Companies.objects.filter(last_update__lte=lte,
                                              last_update__gte=gte).values('cin') \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        elif lte == '' and gte != '':
            total = Companies.objects.filter(last_update__gte=gte).count()
            result = Companies.objects.filter(last_update__gte=gte) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        elif lte != '' and gte == '':
            total = Companies.objects.filter(last_update__lte=lte).count()
            result = Companies.objects.filter(last_update__lte=lte) \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))
        else:
            total = Companies.objects.all().count()
            result = Companies.objects.all() \
                .annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True),
                          znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True),
                          likvidator_issues_count=Count('likvidatorissues', distinct=True),
                          konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True),
                          konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))

    page_num = (page - 1) * per_page

    if len(order_list) > 1 and order_type == '-':
        first = order_list[0].replace('-', '')
        order_list.pop(0)
        result = result.order_by(F(first).desc(nulls_last=True), *order_list)[page_num:(page_num + per_page)]
    elif len(order_list) == 1 and order_type == '-':
        result = result.order_by(F(order_list[0]).desc(nulls_last=True))[page_num:(page_num + per_page)]
    elif order_type == '':
        result = result.order_by(*order_list)[page_num:(page_num + per_page)]

    response = {'items': []}
    pages_count = total // per_page
    if total % per_page != 0:
        pages_count += 1

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': pages_count, 'total': total}

    for row in result:
        if row.or_podanie_issues_count != 0:
            opic = row.or_podanie_issues_count
        else:
            opic = None
        if row.znizenie_imania_issues_count != 0:
            ziic = row.znizenie_imania_issues_count
        else:
            ziic = None
        if row.likvidator_issues_count != 0:
            lic = row.likvidator_issues_count
        else:
            lic = None
        if row.konkurz_vyrovnanie_issues_count != 0:
            kvic = row.konkurz_vyrovnanie_issues_count
        else:
            kvic = None
        if row.konkurz_restrukturalizacia_actors_count != 0:
            krac = row.konkurz_restrukturalizacia_actors_count
        else:
            krac = None
        if row.address_line != "":
            address = row.address_line
        else:
            address = None
        entry = {'cin': row.cin, 'name': row.name, 'br_section': row.br_section, 'address_line': address,
                 'last_update': str(row.last_update), 'or_podanie_issues_count': opic,
                 'znizenie_imania_issues_count': ziic,
                 'likvidator_issues_count': lic,
                 'konkurz_vyrovnanie_issues_count': kvic,
                 'konkurz_restrukturalizacia_actors_count': krac}
        response['items'].append(entry)
    return JsonResponse(response)
