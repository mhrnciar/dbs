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
        return query.delete_query(request)
