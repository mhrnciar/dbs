from django.db import connection
from django.http import JsonResponse
from psycopg2.extensions import AsIs
import pytz
from dateutil import parser


# Create your views here.
def check_str(string):
    return string.split(';')[0]


def index(request):
    if request.method == 'GET':
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

        order_by = params.get('order_by', 'cin').lower()
        if order_by not in ('cin', 'name', 'br_section', 'address_line', 'last_update', 'or_podanie_issues_count',
                            'znizenie_imania_issues_count', 'likvidator_issues_count',
                            'konkurz_vyrovnanie_issues_count', 'konkurz_restrukturalizacia_actors_count'):
            order_by = 'cin'

        order_type = params.get('order_type', 'desc').lower()
        if order_type not in ('asc', 'desc'):
            order_type = 'desc'
        gte = ''
        lte = ''
        q = ''

        if 'last_update_gte' in params:
            try:
                dt = parser.parse(params['last_update_gte']).astimezone(pytz.utc)
                gte = 'date_ge(last_update, \'{}\')'.format(str(dt))
            except ValueError:
                gte = ''
        if 'last_update_lte' in params:
            try:
                dt = parser.parse(params['last_update_lte']).astimezone(pytz.utc)
                lte = 'date_le(last_update, \'{}\')'.format(str(dt))
            except ValueError:
                lte = ''
        if 'query' in params:
            q = '(name LIKE \'%{}%\' OR address_line LIKE \'%{}%\')'.format(check_str(params['query']),
                                                                            check_str(params['query']))

        string = '1 = 1'
        if q != '':
            string = q
            if gte != '' and lte == '':
                string += ' AND ' + gte
            elif gte != '' and lte != '':
                string += ' AND ' + gte + ' AND ' + lte
            elif gte == '' and lte != '':
                string += ' AND ' + lte
        else:
            if gte != '' and lte == '':
                string = gte
            elif gte != '' and lte != '':
                string = gte + ' AND ' + lte
            elif gte == '' and lte != '':
                string = lte

        cursor = connection.cursor()
        query = 'SELECT cin, name, br_section, address_line, last_update, ' \
                'or_podanie_issues_count, ' \
                'znizenie_imania_issues_count, ' \
                'likvidator_issues_count, ' \
                'konkurz_vyrovnanie_issues_count, ' \
                'konkurz_restrukturalizacia_actors_count FROM ov.companies c ' \
                'LEFT JOIN (SELECT cin, count(cin) as or_podanie_issues_count ' \
                'FROM ov.or_podanie_issues GROUP BY cin) o USING (cin) ' \
                'LEFT JOIN (SELECT cin, count(cin) as znizenie_imania_issues_count ' \
                'FROM ov.znizenie_imania_issues GROUP BY cin) z USING (cin) ' \
                'LEFT JOIN (SELECT cin, count(cin) as likvidator_issues_count ' \
                'FROM ov.likvidator_issues GROUP BY cin) l USING (cin) ' \
                'LEFT JOIN (SELECT cin, count(cin) as konkurz_vyrovnanie_issues_count ' \
                'FROM ov.konkurz_vyrovnanie_issues GROUP BY cin) kv USING (cin) ' \
                'LEFT JOIN (SELECT cin, count(cin) as konkurz_restrukturalizacia_actors_count ' \
                'FROM ov.konkurz_restrukturalizacia_actors GROUP BY cin) kr USING (cin) ' \
                'WHERE %s ORDER BY %s %s LIMIT %s OFFSET %s;'
        cursor.execute(query, (AsIs(string), AsIs(order_by), AsIs(order_type), per_page, (per_page * (page - 1))))

        result = cursor.fetchall()
        if result is None:
            return JsonResponse({'Query error (SELECT)!'}, status=404)

        query = "SELECT COUNT(*) FROM ov.companies WHERE %s;"
        cursor.execute(query, (AsIs(string),))

        response = cursor.fetchone()
        if response is None:
            return JsonResponse({'Query error (SELECT COUNT)!'}, status=404)
        total = response[0]

        response = {'items': []}

        pages_count = total // per_page
        if total % per_page != 0:
            pages_count += 1

        response['metadata'] = {'page': page, 'per_page': per_page, 'pages': pages_count, 'total': total}

        if total > 0:
            for row in result:
                entry = {'cin': row[0], 'name': row[1], 'br_section': row[2], 'address_line': row[3],
                         'last_update': str(row[4]), 'or_podanie_issues_count': row[5],
                         'znizenie_imania_issues_count': row[6], 'likvidator_issues_count': row[7],
                         'konkurz_vyrovnanie_issues_count': row[8], 'konkurz_restrukturalizacia_actors_count': row[9]}
                response['items'].append(entry)

        else:
            return JsonResponse(response, status=404)

        return JsonResponse(response, status=200)
