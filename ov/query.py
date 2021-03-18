from django.db import connection
from django.http import JsonResponse
from psycopg2.extensions import AsIs
import datetime
import pytz
from dateutil import parser
import json


# Jednoducha operacia, ktora odstrani zo zadanych parametrov vsetko po ; ak sa nejaka najde - velmi primitivny sposob
# ochrany pred SQL injection
def check_str(string):
    return string.split(';')[0]


def get_query(request):
    params = request.GET

    # Ziskanie cisla strany a poctu vysledkov na stranu, prednastavene hodnoty su page: 1 a per_page: 10. Ak je zadane
    # zaporne cislo alebo string, nastavi sa default hodnota.
    try:
        page = int(params.get('page', 1))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    try:
        per_page = int(params.get('per_page', 10))
    except ValueError:
        per_page = 10
    if per_page < 1:
        per_page = 10

    # Standardne hodnoty pre zoradovanie su registration_date desc, ktore sa nastavia aj v pripade ze je zadany
    # neplatny stlpec alebo sposob zoradenia. Premenna sa nastavi na male pismena, takze je jedno ako je parameter
    # zadany za predpokladu ze je spravny.
    order_by = params.get('order_by', 'registration_date').lower()
    if order_by not in ('id', 'br_court_name', 'kind_name', 'cin', 'registration_date', 'corporate_body_name',
                        'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city'):
        order_by = 'registration_date'

    order_type = params.get('order_type', 'desc').lower()
    if order_type not in ('asc', 'desc'):
        order_type = 'desc'
    gte = ''
    lte = ''
    q = ''

    # Ak boli zadane datumy na filtrovanie, najprv sa zisti, ci su v spravnom tvare tak, ze sa spravi parse a vynimka
    # sa zachyti. Ak su v spravnom tvare, vytvori sa string s parametrom. Query sa skusi premenit na int a ak to ide,
    # hlada sa podla cin, v opacnom pripade je to string a hlada sa podla corporate_body_name a city.
    if 'registration_date_gte' in params:
        try:
            dt = parser.parse(params['registration_date_gte']).astimezone(pytz.utc)
            gte = 'date_ge(registration_date, \'{}\')'.format(str(dt))
        except ValueError:
            gte = ''
    if 'registration_date_lte' in params:
        try:
            dt = parser.parse(params['registration_date_lte']).astimezone(pytz.utc)
            lte = 'date_le(registration_date, \'{}\')'.format(str(dt))
        except ValueError:
            lte = ''
    if 'query' in params:
        try:
            cin = int(params['query'])
            q = 'cin = {}'.format(cin)
        except ValueError:
            q = '(corporate_body_name LIKE \'%{}%\' OR city LIKE \'%{}%\')'.format(check_str(params['query']),
                                                                                   check_str(params['query']))

    # Skladanie stringu podla toho, ktore parametre pre vyhladavanie boli zadane
    string = ''
    if q != '':
        string += 'WHERE ' + q
        if gte != '' and lte == '':
            string += ' AND ' + gte
        elif gte != '' and lte != '':
            string += ' AND ' + gte + ' AND ' + lte
        elif gte == '' and lte != '':
            string += ' AND ' + lte
    else:
        if gte != '' and lte == '':
            string += 'WHERE ' + gte
        elif gte != '' and lte != '':
            string += 'WHERE ' + gte + ' AND ' + lte
        elif gte == '' and lte != '':
            string += 'WHERE ' + lte

    # Vytvori sa kurzor a najprv sa vykona select na vysledky, a potom sa spocitaju vsetky riadky z danej query.
    cursor = connection.cursor()
    query = "SELECT id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, " \
            "br_insertion, text, street, postal_code, city FROM ov.or_podanie_issues %s ORDER BY %s %s " \
            "LIMIT %s OFFSET %s;"
    cursor.execute(query, (AsIs(string), AsIs(order_by), AsIs(order_type), per_page, (per_page * (page - 1))))

    result = cursor.fetchall()
    if result is None:
        return JsonResponse({'Query error (SELECT)!'}, status=404)

    query = "SELECT COUNT(*) FROM ov.or_podanie_issues %s;"
    cursor.execute(query, (AsIs(string),))

    response = cursor.fetchone()
    if response is None:
        return JsonResponse({'Query error (SELECT COUNT)!'}, status=404)
    total = response[0]

    response = {'items': []}

    # Ak je pocet ziskanych zaznamov mensi ako zadany per_page, pocet stran je 1 a vypisu sa vsetky zaznamy (za
    # predpokladu, ze page = 1). Ak je zaznamov viac, vypocita sa pocet stran a ak zostane zvysok po deleni, prida sa
    # este jedna strana, ktora nie je plna.
    pages_count = total // per_page
    if total % per_page != 0:
        pages_count += 1

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': pages_count, 'total': total}

    # Ak vypisujeme stranu, na ktorej su vysledky, vytvori sa pole vysledkov so ziskanymi hodnotami a metadatami na
    # konci. V opacnom pripade sa odosle prazdne pole s metadatami.
    if page <= pages_count:
        for row in result:
            entry = {'id': row[0], 'br_court_name': row[1], 'kind_name': row[2], 'cin': row[3],
                     'registration_date': row[4], 'corporate_body_name': row[5], 'br_section': row[6],
                     'br_insertion': row[7], 'text': row[8], 'street': row[9], 'postal_code': row[10], 'city': row[11]}
            response['items'].append(entry)
    else:
        return JsonResponse(response, status=404)

    return JsonResponse(response, status=200)


def post_query(request):
    # Telo requestu sa dekoduje a pripravi sa dictionary, ktory uklada vsetky chyby. Ak na konci nie je prazdny,
    # odosle sa ako chybova hlaska. Kazdy required string je skontrolovany ci sa nachadza v body, hodnoty, ktore by
    # mali byt int (cin a postal_code aj ked ten sa uklada ako string) sa skusia prekonvertovat na int, a pri datume
    # sa skontroluje ci sa rok zhoduje s aktualnym rokom.
    body_unicode = request.body.decode('utf-8')
    params = json.loads(body_unicode)
    errorstr = {'errors': []}
    year = datetime.date.today().year
    cin = 0

    if 'br_court_name' not in params:
        errorstr['errors'].append({'field': 'br_court_name', 'reasons': ['required']})

    if 'kind_name' not in params:
        errorstr['errors'].append({'field': 'kind_name', 'reasons': ['required']})

    if 'cin' not in params:
        errorstr['errors'].append({'field': 'cin', 'reasons': ['required']})
    else:
        try:
            cin = int(params['cin'])
        except ValueError:
            errorstr['errors'].append({'field': 'cin', 'reasons': ['required', 'not_number']})

    if 'registration_date' not in params:
        errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required']})
    else:
        try:
            dt = parser.parse(params['registration_date']).astimezone(pytz.utc)
            date = datetime.date(dt.year, dt.month, dt.day)
            if date.year != year:
                errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required', 'invalid_range']})
        except ValueError:
            errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required', 'invalid_date']})

    if 'corporate_body_name' not in params:
        errorstr['errors'].append({'field': 'corporate_body_name', 'reasons': ['required']})

    if 'br_section' not in params:
        errorstr['errors'].append({'field': 'br_section', 'reasons': ['required']})

    if 'br_insertion' not in params:
        errorstr['errors'].append({'field': 'br_insertion', 'reasons': ['required']})

    if 'text' not in params:
        errorstr['errors'].append({'field': 'text', 'reasons': ['required']})

    if 'street' not in params:
        errorstr['errors'].append({'field': 'street', 'reasons': ['required']})

    if 'postal_code' not in params:
        errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required']})
    else:
        try:
            int(params['postal_code'])
        except ValueError:
            errorstr['errors'].append({'field': 'postal_code', 'reasons': ['required', 'not_number']})

    if 'city' not in params:
        errorstr['errors'].append({'field': 'city', 'reasons': ['required']})

    if len(errorstr['errors']) != 0:
        return JsonResponse(errorstr, status=422)

    # Pre created_at, updated_at a published_at sa zisti momentalny cas prekonvertovany na UTC. Published_at v databaze
    # ma datum o den pred datumom created_at a update_at s vynulovanym casom, takze published_at sa este upravi na dany
    # tvar. Nakoniec sa este posklada adresa zo street, postal_code a city.
    now = datetime.datetime.now().astimezone(pytz.timezone('UTC'))
    today = str(now)
    published_at = str(datetime.datetime(now.year, now.month, now.day - 1, 0, 0, 0, 0))
    address = params['street'] + ', ' + params['postal_code'] + ' ' + params['city']

    # V bulletin_issues sa v danom roku moze nachadzat iba jeden zaznam s danym number, takze sa najprv zisti ake number
    # ma posledny zadany zaznam, a vkladany sa ulozi s (number + 1). Z vkladania do bulletin_issues sa vrati id
    # vlozeneho zaznamu, ktore sa pouzije pri raw_issues a podanie_issues.
    cursor = connection.cursor()
    count_number = 'SELECT number FROM ov.bulletin_issues WHERE year = %s ORDER BY number DESC'
    cursor.execute(count_number, (year,))
    result = cursor.fetchone()
    if result is None:
        return JsonResponse({'Query error (SELECT bulletin_issues)!'}, status=404)

    number = int(result[0])

    bulletin_params = (year, (number + 1), published_at, today, today)
    insert_bulletin = "INSERT INTO ov.bulletin_issues (year, number, published_at, created_at, updated_at) VALUES " \
                      "(%s, %s, TIMESTAMP %s, TIMESTAMP %s, TIMESTAMP %s) RETURNING id;"
    cursor.execute(insert_bulletin, bulletin_params)
    result = cursor.fetchone()
    if result is None:
        return JsonResponse({'Query error (INSERT bulletin_issues)!'}, status=404)

    bulletin_id = result[0]

    # Vkladanie zaznamu do raw_issues, rovnako ako pri bulletin_issues sa vrati id, ktore sa pouzije pri podanie_issues.
    raw_params = (bulletin_id, '-', '-', today, today)
    insert_raw = "INSERT INTO ov.raw_issues (bulletin_issue_id, file_name, content, created_at, updated_at) VALUES " \
                 "(%s, %s, %s, TIMESTAMP %s, TIMESTAMP %s) RETURNING id;"
    cursor.execute(insert_raw, raw_params)
    result = cursor.fetchone()
    if result is None:
        return JsonResponse({'Query error (INSERT raw_issues)!'}, status=404)

    raw_id = result[0]

    # Vkladanie vsetkych dat do podanie_issues spolu s id, ktore sa vratili z bulletin_issues a raw_issues. Aj toto
    # vkladanie vrati id, pomocou ktoreho sa skontroluje ci zaznam bol naozaj vlozeny do tabulky.
    insert_params = (bulletin_id, raw_id, '-', '-', params['br_court_name'], '-', params['kind_name'], cin,
                     params['registration_date'], params['corporate_body_name'], params['br_section'],
                     params['br_insertion'], params['text'], today, today, address, params['street'],
                     params['postal_code'], params['city'])
    insert_podanie = "INSERT INTO ov.or_podanie_issues (bulletin_issue_id, raw_issue_id, br_mark, br_court_code, " \
                     "br_court_name, kind_code, kind_name, cin, registration_date, corporate_body_name, br_section, " \
                     "br_insertion, text, created_at, updated_at, address_line, street, postal_code, city) VALUES " \
                     "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TIMESTAMP %s, " \
                     "TIMESTAMP %s, %s, %s, %s, %s) RETURNING id;"
    cursor.execute(insert_podanie, insert_params)
    result = cursor.fetchone()
    if result is None:
        return JsonResponse({'Query error (INSERT or_podanie_issues)!'}, status=404)

    podanie_id = result[0]

    # Nakoniec sa ziska vlozeny zaznam a vypise sa spolu s id, s ktorym bol vlozeny do podanie_issues.
    query = "SELECT id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, " \
            "br_insertion, text, street, postal_code, city FROM ov.or_podanie_issues WHERE id = %s;"
    cursor.execute(query, (podanie_id,))
    result = cursor.fetchone()
    if result is None:
        return JsonResponse({'Query error (SELECT or_podanie_issues)!'}, status=404)

    response = {'response': {'id': result[0], 'br_court_name': result[1], 'kind_name': result[2], 'cin': result[3],
                             'registration_date': result[4], 'corporate_body_name': result[5], 'br_section': result[6],
                             'br_insertion': result[7], 'text': result[8], 'street': result[9],
                             'postal_code': result[10], 'city': result[11]}}

    return JsonResponse(response, status=201)


def delete_query(request):
    # Najprv sa ziska id z URL a skusi sa prekonvertovat na int. Ak to nie je int, vypise sa chybova hlaska.
    path = request.path.split('/')
    num = path[len(path)-1]
    try:
        num = int(num)
    except ValueError:
        num = None

    if num is not None:
        # Zisti sa ci dany zaznam existuje a ak nie, vypise sa chybova hlaska. Inac sa ziskaju id na bulletin_issues a
        # raw_issues a skontroluje sa, ci na ne neodkazuje viac zaznamov. Ak ano, ponechaju sa a ak na ne odkazuje iba
        # zaznam, ktory ma byt vymazany, zmazu sa aj ony. Zaznam z podanie_issues je zmazany vzdy za predpokladu ze
        # existuje. V pripade uspechu sa vrati prazdna sprava s kodom 204.
        cursor = connection.cursor()
        exist_query = 'SELECT EXISTS (SELECT TRUE FROM ov.or_podanie_issues WHERE id = %s);'
        cursor.execute(exist_query, (num,))
        exists = cursor.fetchone()
        if exists is None:
            return JsonResponse({'Query error (SELECT EXISTS)!'}, status=404)

        if exists[0]:
            id_query = 'SELECT bulletin_issue_id, raw_issue_id FROM ov.or_podanie_issues WHERE id = %s;'
            cursor.execute(id_query, (num,))
            response = cursor.fetchone()
            if response is None:
                return JsonResponse({'Query error (SELECT bulletin_id, raw_id)!'}, status=404)
            bulletin_issue = response[0]
            raw_issue = response[1]

            bulletin_query = 'SELECT COUNT(*) FROM ov.or_podanie_issues WHERE bulletin_issue_id = %s;'
            cursor.execute(bulletin_query, (bulletin_issue,))
            bulletin_count = cursor.fetchone()
            if bulletin_count is None:
                return JsonResponse({'Query error (SELECT bulletin_issues COUNT)!'}, status=404)

            raw_query = 'SELECT COUNT(*) FROM ov.or_podanie_issues WHERE raw_issue_id = %s;'
            cursor.execute(raw_query, (raw_issue,))
            raw_count = cursor.fetchone()
            if raw_count is None:
                return JsonResponse({'Query error (SELECT raw_issues COUNT)!'}, status=404)

            delete_podanie = 'DELETE FROM ov.or_podanie_issues WHERE id = %s;'
            cursor.execute(delete_podanie, (num,))

            # Zistovanie kolko zaznamov odkazuje na zaznamy v bulletin_issues a raw_issues.
            if bulletin_count[0] == 1:
                delete_bulletin = 'DELETE FROM ov.bulletin_issues WHERE id = %s;'
                cursor.execute(delete_bulletin, (bulletin_issue,))
            if raw_count[0] == 1:
                delete_raw = 'DELETE FROM ov.raw_issues WHERE id = %s;'
                cursor.execute(delete_raw, (raw_issue,))

            return JsonResponse({}, status=204)

        else:
            return JsonResponse({'error': {'message': 'Zaznam neexistuje'}}, status=404)

    else:
        return JsonResponse({'error': {'message': 'Nebolo zadane ID'}}, status=422)
