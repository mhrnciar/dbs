# Generated by Django 3.1.6 on 2021-03-18 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(sql="INSERT INTO ov.companies (cin, name, br_section, address_line, created_at, "
                          "updated_at, last_update) SELECT DISTINCT ON (cin) "
                          "cin, "
                          "corporate_body_name, "
                          "br_section, "
                          "coalesce(address_line, concat_ws(' ', concat_ws(', ', street, postal_code), city)), "
                          "current_timestamp, "
                          "current_timestamp, "
                          "last_value(updated_at) "
                          "OVER(PARTITION BY cin ORDER BY updated_at DESC) "
                          "FROM ov.or_podanie_issues WHERE cin IS NOT NULL;",
                          reverse_sql='DROP TABLE IF EXISTS ov.companies;')
    ]
