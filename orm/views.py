from django.shortcuts import render
from . import submissions, companies
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@csrf_exempt
def orm_submissions(request):
    if request.method == 'GET':
        return submissions.get(request)

    elif request.method == 'POST':
        return submissions.post(request)

    elif request.method == 'PUT':
        return submissions.put(request)

    elif request.method == 'DELETE':
        return submissions.delete(request)


@csrf_exempt
def orm_companies(request):
    if request.method == 'GET':
        return companies.get(request)
