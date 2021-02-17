from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from datetime import *


# Create your views here.
def index(request):
    query = "SELECT date_trunc('second', current_timestamp - pg_postmaster_start_time()) as uptime;"
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchone()
    t = timedelta(seconds=rows[0].total_seconds())
    result = {"pgsql": {"uptime": str(t)}}
    return JsonResponse(result)
