from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser


# Create your views here.
def get_entries(request):
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    order_by = request.GET.get('order_by', 'registration_date')
    order_type = request.GET.get('order_type', 'desc')
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
    return JsonResponse(response)


def index(request):
    if request.method == 'GET':
        return get_entries(request)

    elif request.method == 'POST':
        return JsonResponse({'method': 'post'})

    elif request.method == 'DELETE':
        num = request.GET.get('id', None)
        if num is not None:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM ov.or_podanie_issues WHERE id = ' + num + ';')
        return JsonResponse({'method': 'delete'})
