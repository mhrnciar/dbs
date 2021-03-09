from django.db import connection
from django.http import JsonResponse
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

    order_by = params.get('order_by', 'registration_date')
    order_type = params.get('order_type', 'desc')
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

    # String na stlpce, ktore chceme ziskat
    select = 'id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, ' \
             'text, street, postal_code, city'

    cursor = connection.cursor()
    query_params = (select, string, order_by, order_type)
    query = "SELECT %s FROM ov.or_podanie_issues %s ORDER BY %s %s;" % query_params
    cursor.execute(query)

    result = cursor.fetchall()
    response = {'items': []}

    # Ak je pocet ziskanych zaznamov mensi ako zadany per_page, pocet stran je 1 a vypisu sa vsetky zaznamy (za
    # predpokladu, ze page = 1). Ak je zaznamov viac, vypocita sa pocet stran a ak zostane zvysok po deleni, prida sa
    # este jedna strana, ktora nie je plna.
    if len(result) < per_page:
        count = len(result)
        pages_count = 1
    else:
        pages_count = len(result) // per_page
        count = per_page
        if len(result) % per_page != 0:
            pages_count += 1
            if page == pages_count:
                count = len(result) % per_page

    response['metadata'] = {'page': page, 'per_page': per_page, 'pages': pages_count, 'total': len(result)}

    # Ak vypisujeme stranu, na ktorej su vysledky, vytvori sa pole vysledkov so ziskanymi hodnotami a metadata na konci.
    # V opacnom pripade sa odosle prazdne pole s metadatami.
    if per_page * (page - 1) < len(result):
        for p in range(count):
            i = p + (per_page * (page - 1))
            entry = {'id': result[i][0], 'br_court_name': result[i][1], 'kind_name': result[i][2], 'cin': result[i][3],
                     'registration_date': result[i][4], 'corporate_body_name': result[i][5], 'br_section': result[i][6],
                     'br_insertion': result[i][7], 'text': result[i][8], 'street': result[i][9],
                     'postal_code': result[i][10], 'city': result[i][11]}
            response['items'].append(entry)
    else:
        return JsonResponse(response, status=404)

    return JsonResponse(response, status=200)


def post_query(request):
    # Ziskanie a dekodovanie body requestu a priprava dictionary, ktory uklada vsetky chyby. Ak na konci nie je prazdny,
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
        if isinstance(params['cin'], int):
            cin = params['cin']
        else:
            errorstr['errors'].append({'field': 'cin', 'reasons': ['required', 'not_number']})

    if 'registration_date' not in params:
        errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required']})
    else:
        date = params['registration_date'].split('-')
        if int(date[0]) < year or int(date[0]) > year:
            errorstr['errors'].append({'field': 'registration_date', 'reasons': ['required', 'invalid_range']})

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

    # Pre created_at, updated_at a published_at sa zisti momentalny cas prekonvertovany na UTC. Published_at mal datum
    # o den pred datumom created_at a update_at s vynulovanym casom, takze published_at sa este upravi na dany tvar.
    # Nakoniec sa este posklada adresa zo street, postal_code a city.
    now = datetime.datetime.now().astimezone(pytz.timezone('UTC'))
    today = str(now)
    published_at = str(datetime.datetime(now.year, now.month, now.day - 1, 0, 0, 0, 0))
    year = datetime.date.today().year
    address = params['street'] + ', ' + params['postal_code'] + ' ' + params['city']

    # V bulletin_issues sa v danom roku moze nachadzat iba jeden zaznam s danym number, takze sa najprv zisti ake number
    # ma posledny zadany zaznam, a vkladany sa ulozi s (number + 1). Z vkladania do bulletin_issues sa vrati id
    # vlozeneho zaznamu, ktore sa pouzije pri raw_issues a podanie_issues.
    cursor = connection.cursor()
    count_number = 'SELECT * FROM ov.bulletin_issues WHERE year = %d ORDER BY number DESC' % (year,)
    cursor.execute(count_number)
    result = cursor.fetchone()
    number = int(result[2])

    bulletin_params = (year, (number + 1), published_at, today, today)
    insert_bulletin = "INSERT INTO ov.bulletin_issues (year, number, published_at, created_at, updated_at) VALUES " \
                      "(%d, '%s', TIMESTAMP '%s', TIMESTAMP '%s', TIMESTAMP '%s') RETURNING id;" % bulletin_params
    cursor.execute(insert_bulletin)
    bulletin_id = cursor.fetchone()[0]

    # Vkladanie zaznamu do raw_issues, rovnako ako pri bulletin_issues sa vrati id, ktore sa pouzije pri podanie_issues.
    raw_params = (bulletin_id, '-', '-', today, today)
    insert_raw = "INSERT INTO ov.raw_issues (bulletin_issue_id, file_name, content, created_at, updated_at) VALUES " \
                 "(%d, '%s', '%s', TIMESTAMP '%s', TIMESTAMP '%s') RETURNING id;" % raw_params
    cursor.execute(insert_raw, raw_params)
    raw_id = cursor.fetchone()[0]

    # Vkladanie vsetkych dat do podanie_issues spolu s id, ktore sa vratili z bulletin_issues a raw_issues. Aj toto
    # vkladanie vrati id, pomocou ktoreho sa skontroluje ci zaznam bol naozaj vlozeny do tabulky.
    insert_params = (bulletin_id, raw_id, '-', '-', params['br_court_name'], '-', params['kind_name'], cin,
                     params['registration_date'], params['corporate_body_name'], params['br_section'],
                     params['br_insertion'], params['text'], today, today, address, params['street'],
                     params['postal_code'], params['city'])
    insert_podanie = "INSERT INTO ov.or_podanie_issues (bulletin_issue_id, raw_issue_id, br_mark, br_court_code, " \
                     "br_court_name, kind_code, kind_name, cin, registration_date, corporate_body_name, br_section, " \
                     "br_insertion, text, created_at, updated_at, address_line, street, postal_code, city) VALUES " \
                     "(%d, %d, '%s', '%s', '%s', '%s', '%s', %d, '%s', '%s', '%s', '%s', '%s', TIMESTAMP '%s', " \
                     "TIMESTAMP '%s', '%s', '%s', '%s', '%s') RETURNING id;" % insert_params
    cursor.execute(insert_podanie)
    podanie_id = cursor.fetchone()[0]

    # Nakoniec sa ziska vlozeny zaznam a vypise sa spolu s id, s ktorym bol vlozeny do podanie_issues.
    select = 'id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, ' \
             'text, street, postal_code, city'
    query_params = (select, podanie_id)
    query = "SELECT %s FROM ov.or_podanie_issues WHERE id = %d;" % query_params
    cursor.execute(query)
    result = cursor.fetchone()

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
        exist_query = 'SELECT EXISTS (SELECT TRUE FROM ov.or_podanie_issues WHERE id = %d);' % (num,)
        cursor.execute(exist_query)
        exists = cursor.fetchone()

        if exists[0]:
            id_query = 'SELECT bulletin_issue_id, raw_issue_id FROM ov.or_podanie_issues WHERE id = %d;' % (num,)
            cursor.execute(id_query)
            response = cursor.fetchone()
            bulletin_issue = response[0]
            raw_issue = response[1]

            bulletin_query = 'SELECT * FROM ov.or_podanie_issues WHERE bulletin_issue_id = %d;' % (bulletin_issue,)
            cursor.execute(bulletin_query)
            bulletin_count = cursor.fetchall()

            raw_query = 'SELECT * FROM ov.or_podanie_issues WHERE raw_issue_id = %d;' % (raw_issue,)
            cursor.execute(raw_query)
            raw_count = cursor.fetchall()

            delete_podanie = 'DELETE FROM ov.or_podanie_issues WHERE id = %d;' % (num,)
            cursor.execute(delete_podanie)

            # Zistovanie kolko zaznamov odkazuje na zaznamy v bulletin_issues a raw_issues.
            if len(bulletin_count) == 1:
                delete_bulletin = 'DELETE FROM ov.bulletin_issues WHERE id = %d;' % (bulletin_issue,)
                cursor.execute(delete_bulletin)
            if len(raw_count) == 1:
                delete_raw = 'DELETE FROM ov.raw_issues WHERE id = %d;' % (raw_issue,)
                cursor.execute(delete_raw)

            return JsonResponse({}, status=204)

        else:
            return JsonResponse({'error': {'message': 'Zaznam neexistuje'}}, status=404)

    else:
        return JsonResponse({'error': {'message': 'Nebolo zadane ID'}}, status=422)
