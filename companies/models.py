from django.db import models


# Create your models here.
class Companies(models.Model):
    cin = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=300, null=True)
    br_section = models.CharField(max_length=50, null=True)
    address_line = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_update = models.DateTimeField()
