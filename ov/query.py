from django.db import connection
from django.http import JsonResponse
import datetime
import json


def check_str(string):
    return string.split(';')[0]


def get_query(request):
    params = request.GET
    page = int(params.get('page', 1))
    per_page = int(params.get('per_page', 10))
    order_by = params.get('order_by', 'registration_date')
    order_type = params.get('order_type', 'desc')
    gte = ''
    lte = ''
    q = ''

    if 'registration_date_gte' in params:
        gte = 'date_ge(registration_date, \'{}\')'.format(params['registration_date_gte'])
    if 'registration_date_lte' in params:
        lte = 'date_le(registration_date, \'{}\')'.format(params['registration_date_lte'])
    if 'query' in params:
        q = 'corporate_body_name = \'{}\' OR city = \'{}\''.format(check_str(params['query']), params['query'])

    query = "id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, " \
            "text, street, postal_code, city"
    cursor = connection.cursor()
    cursor.execute('SELECT {} FROM ov.or_podanie_issues WHERE {} AND {} ORDER BY {} {};'.format(query, gte, lte,
                                                                                                order_by, order_type))
    result = cursor.fetchall()
    response = {'items': []}
    count = per_page

    if len(result) < per_page:
        count = len(result)

    for i in range(count):
        entry = {'id': result[i][0], 'br_court_name': result[i][1], 'kind_name': result[i][2], 'cin': result[i][3],
                 'registration_date': result[i][4], 'corporate_body_name': result[i][5], 'br_section': result[i][6],
                 'br_insertion': result[i][7], 'text': result[i][8], 'street': result[i][9],
                 'postal_code': result[i][10], 'city': result[i][11]}
        response['items'].append(entry)

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': 1, 'total': len(result)}
    return JsonResponse(response, status=200)


def post_query(request):
    body_unicode = request.body.decode('utf-8')
    params = json.loads(body_unicode)
    errorstr = {'errors': []}
    cin = 0
    postal_code = 0

    if 'br_court_name' not in params:
        errorstr['errors'].append({'field': 'br_court_name', 'reasons': ['required']})

    if 'kind_name' not in params:
        errorstr['errors'].append({'field': 'kind_name', 'reasons': ['required']})

    if 'cin' not in params:
        errorstr['errors'].append({'field': 'cin', 'reasons': ['required']})
    else:
        try:
            cin = int(params['cin'])
        except ValueError:
            errorstr['errors'].append({'field': 'cin', 'reasons': ['required', 'not_number']})

    if 'registration_date' not in params:
        errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required']})
    else:
        date = params['registration_date'].split('-')
        year = datetime.date.today().year
        if int(date[0]) < year or int(date[0]) > year:
            errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required', 'invalid_range']})

    if 'corporate_body_name' not in params:
        errorstr['errors'].append({'field': 'corporate_body_name', 'reasons': ['required']})

    if 'br_section' not in params:
        errorstr['errors'].append({'field': 'br_section', 'reasons': ['required']})

    if 'br_insertion' not in params:
        errorstr['errors'].append({'field': 'br_insertion', 'reasons': ['required']})

    if 'text' not in params:
        errorstr['errors'].append({'field': 'text', 'reasons': ['required']})

    if 'street' not in params:
        errorstr['errors'].append({'field': 'street', 'reasons': ['required']})

    if 'postal_code' not in params:
        errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required']})
    else:
        try:
            int(params['postal_code'])
        except ValueError:
            errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required', 'not_number']})

    if 'city' not in params:
        errorstr['errors'].append({'field': 'city', 'reasons': ['required']})

    if len(errorstr['errors']) != 0:
        return JsonResponse(errorstr, status=422)

    today = '\'' + str(datetime.datetime.now()) + '\''
    year = datetime.date.today().year
    address = params['street'] + ', ' + params['postal_code'] + ' ' + params['city']

    cursor = connection.cursor()
    cursor.execute("INSERT INTO ov.bulletin_issues (year, number, published_at, created_at, updated_at) VALUES ({}, {}, "
                   "TIMESTAMP {}, TIMESTAMP {}, TIMESTAMP {}) RETURNING id;".format(year, 26, today, today, today))
    bulletin_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO ov.raw_issues (bulletin_issue_id, file_name, content, created_at, updated_at) VALUES "
                   "({}, '{}', '{}', TIMESTAMP {}, TIMESTAMP {}) RETURNING id;".format(bulletin_id, '-', '-', today, today))
    raw_id = cursor.fetchone()[0]

    insert_query = "INSERT INTO ov.or_podanie_issues (bulletin_issue_id, raw_issue_id, br_mark, br_court_code, " \
                   "br_court_name, kind_code, kind_name, cin, registration_date, corporate_body_name, br_section, " \
                   "br_insertion, text, created_at, updated_at, address_line, street, postal_code, city) VALUES " \
                   "({}, {}, '{}', '{}', '{}', '{}', '{}', {}, '{}', '{}', '{}', '{}', '{}', TIMESTAMP {}, TIMESTAMP {}, '{}', '{}', '{}', '{}') RETURNING id;".format(
                    bulletin_id, raw_id, '-', '-', params['br_court_name'], '-', params['kind_name'], cin,
                    params['registration_date'], params['corporate_body_name'], params['br_section'],
                    params['br_insertion'], params['text'], today, today, address, params['street'],
                    params['postal_code'], params['city'])

    cursor.execute(insert_query)
    podanie_id = cursor.fetchone()[0]
    query = "id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, " \
            "text, street, postal_code, city"

    cursor.execute('SELECT {} FROM ov.or_podanie_issues WHERE id = {};'.format(query, str(podanie_id)))
    result = cursor.fetchone()
    response = {'response': {'id': result[0], 'br_court_name': result[1], 'kind_name': result[2], 'cin': result[3],
                             'registration_date': result[4], 'corporate_body_name': result[5], 'br_section': result[6],
                             'br_insertion': result[7], 'text': result[8], 'street': result[9],
                             'postal_code': result[10], 'city': result[11]}}

    return JsonResponse(response, status=201)


def delete_query(request):
    num = request.GET.get('id', None)
    if num is not None:
        cursor = connection.cursor()
        cursor.execute('SELECT EXISTS (SELECT TRUE FROM ov.or_podanie_issues WHERE id = {});'.format(num))
        exists = cursor.fetchone()

        if exists[0]:
            cursor.execute('SELECT bulletin_issue_id, raw_issue_id FROM ov.or_podanie_issues WHERE id = {};'.format(num))
            response = cursor.fetchone()
            bulletin_issue = response[0]
            raw_isssue = response[1]
            cursor.execute('DELETE FROM ov.or_podanie_issues WHERE id = {};'.format(num))
            cursor.execute('DELETE FROM ov.raw_issues WHERE id = {};'.format(raw_isssue))
            cursor.execute('DELETE FROM ov.bulletin_issues WHERE id = {};'.format(bulletin_issue))
            return JsonResponse({}, status=204)

        else:
            return JsonResponse({'error': {'message': 'Zaznam neexistuje'}}, status=404)

    else:
        return JsonResponse({'error': {'message': 'Nebolo zadane ID'}}, status=422)
