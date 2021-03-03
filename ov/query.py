from django.db import connection
from django.http import HttpResponse, JsonResponse
import datetime


def get_query(request):
    params = request.GET
    page = int(params.get('page', 1))
    per_page = int(params.get('per_page', 10))
    order_by = params.get('order_by', 'registration_date')
    order_type = params.get('order_type', 'desc')

    if 'registration_date_gte' in params:
        gte = 'date_ge ' + params['registration_date_gte']
    if 'registration_date_lte' in params:
        lte = 'date_le ' + params['registration_date_lte']
    if 'query' in params:
        q = 'corporate_body_name = \'' + params['query'] + '\' OR city = \'' + params['query'] + '\''

    query = "id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, " \
            "text, street, postal_code, city"
    cursor = connection.cursor()
    cursor.execute('SELECT ' + query + ' FROM or_podanie_issues ORDER BY ' + order_by + ' ' + order_type + ' LIMIT '
                   + str(per_page) + ' OFFSET ' + str(per_page * (page - 1)) + ';')
    result = cursor.fetchall()
    response = {'items': []}

    for i in range(per_page):
        entry = {'id': result[i][0], 'br_court_name': result[i][1], 'kind_name': result[i][2], 'cin': result[i][3],
                 'registration_date': result[i][4], 'corporate_body_name': result[i][5], 'br_section': result[i][6],
                 'br_insertion': result[i][7], 'text': result[i][8], 'street': result[i][9],
                 'postal_code': result[i][10], 'city': result[i][11]}
        response['items'].append(entry)

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': 1, 'total': 1001}
    return JsonResponse(response, status=200)


def post_query(request):
    params = request.GET
    errorstr = {'errors': []}

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

    if 'text' not in params:
        errorstr['errors'].append({'field': 'text', 'reasons': ['required']})

    if 'street' not in params:
        errorstr['errors'].append({'field': 'street', 'reasons': ['required']})

    if 'postal_code' not in params:
        errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required']})
    else:
        try:
            postal_code = int(params['postal_code'])
        except ValueError:
            errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required', 'not_number']})

    if 'city' not in params:
        errorstr['errors'].append({'field': 'city', 'reasons': ['required']})

    if len(errorstr['errors']) != 0:
        return JsonResponse(errorstr, status=422)

    return JsonResponse({'entry': params['br_court_name']}, status=201)

