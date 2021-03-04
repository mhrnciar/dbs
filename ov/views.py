from django.shortcuts import render
from . import query
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@csrf_exempt
def index(request):
    if request.method == 'GET':
        return query.get_query(request)

    elif request.method == 'POST':
        return query.post_query(request)

    elif request.method == 'DELETE':
        return query.delete_query(request)
