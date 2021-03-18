from django.db import connection

cursor = connection.cursor()

cursor.execute('DROP TABLE IF EXISTS ov.companies; '
               'CREATE TABLE ov.companies ('
               'cin bigint NOT NULL, '
               'name varchar(300), '
               'br_section varchar(50), '
               'address_line varchar(300), '
               'created_at timestamp without time zone, '
               'updated_at timestamp without time zone, '
               'last_update timestamp without time zone, '
               'PRIMARY KEY (cin));')

cursor.execute("INSERT INTO ov.companies (cin, name, br_section, address_line, created_at, updated_at, last_update) "
               "SELECT DISTINCT ON (cin) "
               "cin, "
               "corporate_body_name, "
               "br_section, "
               "coalesce(address_line, concat_ws(' ', concat_ws(', ', street, postal_code), city)), "
               "created_at, "
               "updated_at, "
               "max(updated_at) OVER(PARTITION BY cin ORDER BY updated_at DESC) "
               "FROM ov.or_podanie_issues WHERE cin IS NOT NULL;")

cursor.execute("INSERT INTO ov.companies (cin, name, br_section, address_line, created_at, updated_at, last_update) "
               "SELECT DISTINCT ON (cin) "
               "cin, "
               "corporate_body_name, "
               "br_section, "
               "concat_ws(' ', concat_ws(', ', street, postal_code), city), "
               "created_at, "
               "updated_at, "
               "max(updated_at) OVER(PARTITION BY cin ORDER BY updated_at DESC) "
               "FROM ov.likvidator_issues WHERE cin IS NOT NULL ON CONFLICT (cin) DO NOTHING;")

cursor.execute("INSERT INTO ov.companies (cin, name, address_line, created_at, updated_at, last_update) "
               "SELECT DISTINCT ON (cin) "
               "cin, "
               "corporate_body_name, "
               "concat_ws(' ', concat_ws(', ', street, postal_code), city), "
               "created_at, "
               "updated_at, "
               "max(updated_at) OVER(PARTITION BY cin ORDER BY updated_at DESC) "
               "FROM ov.konkurz_vyrovnanie_issues WHERE cin IS NOT NULL ON CONFLICT (cin) DO NOTHING;")

cursor.execute("INSERT INTO ov.companies (cin, name, br_section, address_line, created_at, updated_at, last_update) "
               "SELECT DISTINCT ON (cin) "
               "cin, "
               "corporate_body_name, "
               "br_section, "
               "concat_ws(' ', concat_ws(', ', street, postal_code), city), "
               "created_at, "
               "updated_at, "
               "max(updated_at) OVER(PARTITION BY cin ORDER BY updated_at DESC) "
               "FROM ov.znizenie_imania_issues WHERE cin IS NOT NULL ON CONFLICT (cin) DO NOTHING;")

cursor.execute("INSERT INTO ov.companies (cin, name, address_line, created_at, updated_at, last_update) "
               "SELECT DISTINCT ON (cin) "
               "cin, "
               "corporate_body_name, "
               "concat_ws(' ', concat_ws(', ', street, postal_code), city), "
               "created_at, "
               "updated_at, "
               "max(updated_at) OVER(PARTITION BY cin ORDER BY updated_at DESC) "
               "FROM ov.konkurz_restrukturalizacia_actors WHERE cin IS NOT NULL ON CONFLICT (cin) DO NOTHING;")
