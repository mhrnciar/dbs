from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
from . import query
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status


# Create your views here.
def index(request):
    if request.method == 'GET':
        return query.get_query(request)

    elif request.method == 'POST':
        return query.post_query(request)

    elif request.method == 'DELETE':
        num = request.GET.get('id', None)
        if num is not None:
            cursor = connection.cursor()
            cursor.execute('SELECT bulletin_issue_id, raw_issue_id FROM ov.or_podanie_issues WHERE id = ' + num + ';')
            response = cursor.fetchone()
            bulletin_issue = response[0]
            raw_isssue = response[1]
            cursor.execute('DELETE FROM ov.or_podanie_issues WHERE id = ' + num + ';')
            cursor.execute('DELETE FROM ov.bulletin_issues WHERE id = ' + bulletin_issue + ';')
            cursor.execute('DELETE FROM ov.raw_issues WHERE id = ' + raw_isssue + ';')
        return JsonResponse({'method': 'delete'})
