from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^ov/submissions/.*$', views.orm_submissions),
    re_path(r'^companies/.*$', views.orm_companies),
]
