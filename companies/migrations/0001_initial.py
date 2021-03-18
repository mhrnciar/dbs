# Generated by Django 3.1.6 on 2021-03-18 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(sql='CREATE TABLE ov.companies (cin bigint NOT NULL,'
                              'name varchar(300),'
                              'br_section varchar(50),'
                              'address_line varchar(300),'
                              'created_at timestamp without time zone,'
                              'updated_at timestamp without time zone,'
                              'last_update timestamp without time zone,'
                              'PRIMARY KEY (cin));',
                          reverse_sql='DROP TABLE IF EXISTS ov.companies;')
    ]
