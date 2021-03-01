from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

# Create your views here.
def index(request):
    if request.method == 'GET':
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM ov.bulletin_issues;')
        result = cursor.fetchall()
        return JsonResponse({'result': [{'method': 'get'}, {'bulletin_issues count': result[0][0]}]})

    elif request.method == 'POST':
        return JsonResponse({'method': 'post'})

    elif request.method == 'DELETE':
        return JsonResponse({'method': 'delete'})
