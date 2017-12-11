from sys import argv
import sqlite3
import datetime
import pytz
import requests
import os
from lxml import html
from itertools import product


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def day_calculator(date):
    # converts a date object into the corresponding date_id
    return (date - FIRST_DATE).days + 1


def find_today():
    # finds the latest day based on the mastercard definition
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    if now.hour < 14:
        today = now.date() - datetime.timedelta(days=1)
    else:
        today = now.date()
    return day_calculator(today)


def date_calculator(day):
    # converts a date_id into a date
    return FIRST_DATE + datetime.timedelta(day - 1)


def master_date_string(date):
    # converts a date object into the mastercard format
    return date.strftime('%Y-%m-%d')


def visa_date_string(date):
    # converts a date object into the visa format
    return date.strftime('%d/%m/%Y')


def find_visa_set():
    # creates a set of all codes that visa provides rates for
    m_rate_url = 'https://www.visaeurope.com/making-payments/exchange-rates'
    page = requests.get(m_rate_url)
    tree = html.fromstring(page.content)
    cur_xpath = ("//select"
                 "[@name="
                 "'ctl00$ctl00$MainContent$MainContent$ctl00$ddlCardCurrency']"
                 "/option")
    options = tree.xpath(cur_xpath)
    codes = {o.attrib['value'] for o in options if len(o.attrib['value']) == 3}
    return codes


def find_master_set():
    # creates a set of all codes that mastercard provides rates for
    r = requests.get(MASTERCARD + SETTLEMENT,
                     headers={"referer": MASTERCARD + SUPPORT})

    JSON = r.json()
    codes = list()
    codes = {x['alphaCd'] for x in JSON['data']['currencies']}
    return codes


def get_code_list(cur):
    # gets the list of all codes from the database
    # codes[i]+1 are the code ids
    cur.execute('SELECT code FROM Currency_Codes')
    code_tuples = cur.fetchall()
    print("I got the code list!")
    return [x[0] for x in code_tuples]


def create_all_combos(cur, l1, l2):
    cur.execute('''CREATE TABLE All_Combos (
    card_id INTEGER NOT NULL,
    trans_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    UNIQUE(card_id, trans_id, date_id)
    );''')

    cur.execute('BEGIN TRANSACTION')
    print("generating all combos")
    all_combos = ((x, y, z) for x, y, z in product(l1, l1, l2) if x != y)
    cur.executemany('''INSERT into All_Combos (card_id, trans_id, date_id)
                       Values (?, ?, ?)''', (all_combos))


def find_missing_combos(cur, vnm, mnv):
    print("finding missing combos")
    sql = '''CREATE TABLE Missing AS
    SELECT card_id,trans_id,date_id FROM All_Combos
    EXCEPT
    SELECT card_id, trans_id, date_id FROM Rates
    UNION
    SELECT card_id,trans_id,date_id FROM Rates
    WHERE (trans_id NOT IN {} AND card_id NOT IN {} AND mastercard IS NULL)
    OR (trans_id NOT IN {} AND card_id NOT IN {} AND visa IS NULL)
    AND date_id > {};
    '''.format(vnm, vnm, mnv, mnv, TODAY - 363)
    cur.execute(sql)
    cur.execute("SELECT Count(*) FROM Missing")
    print("Number missing", cur.fetchone()[0])


def fetch_data(cur):
    print("translating to codes")
    cur.execute('''
    CREATE TABLE Missing_Codes AS
    Select card , Currency_Codes.code as trans, date_id
    FROM (
    Select Currency_Codes.code as card, Missing.trans_id, Missing.date_id
    FROM Missing
    JOIN Currency_Codes
    ON (Missing.card_id = Currency_Codes.rowid)
    )
    JOIN Currency_Codes
    ON (trans_id = Currency_Codes.rowid)
    ''')
    cur.execute('select * from Missing_Codes')
    return cur.fetchall()


def get_mvb(card_c, trans_c):
    # Is the currency supplied just by mastercard, just visa or both?
    # stops unnessecary requests
    # the empty set returns false
    if {card_c, trans_c} & master_only:
        return "m"
    elif {card_c, trans_c} & visa_only:
        return "v"
    else:
        return "b"


def index_tuple(l1, l2):
    return tuple(map(lambda x: l1.index(x) + 1, l2))


def drop_tables(cur, tables):
    for table in tables:
        cur.execute("DROP TABLE IF EXISTS {}".format(table))


MASTERCARD = 'https://www.mastercard.co.uk/'
SETTLEMENT = 'settlement/currencyrate/settlement-currencies'
SUPPORT = 'en-gb/consumers/get-support/convert-currency.html'
FIRST_DATE = datetime.date(2016, 10, 14)
if __name__ == '__main__':
    N = int(argv[1])
    print(N)
    con = sqlite3.connect('CardRates.db')
    cur = con.cursor()
    TODAY = find_today()
    all_db_codes = get_code_list(cur)
    master_set = find_master_set()
    visa_set = find_visa_set()
    visa_only = visa_set - master_set
    master_only = master_set - visa_set
    all_online_codes = master_set | visa_set
    missing_codes = all_online_codes - set(all_db_codes)
    print("Visa only:", visa_only)
    print("Master only:", master_only)
    print("Missing from DB:", missing_codes)
    temp_tabs = ("All_Combos", "Missing", "Missing_Codes")
    drop_tables(cur, temp_tabs)
    create_all_combos(cur, range(1, len(all_db_codes) + 1),
                      range(TODAY - 363, TODAY + 1)
                      )
    find_missing_combos(cur, index_tuple(list(all_db_codes), visa_only),
                        index_tuple(list(all_db_codes), master_only)
                        )
    data = fetch_data(cur)
    drop_tables(cur, temp_tabs)
    con.close()
    chunked = chunkify(data, N)
    os.mkdir('input')
    os.mkdir('output')
    print(len(chunked))
    for i in range(0, N):
        print(len(chunked[i]))
    for (i, chunk) in enumerate(chunked):
        with open('input/' + str(i) + '.csv', 'w') as f:
            for item in chunk:
                date = date_calculator(item[2])
                card_c = item[0]
                trans_c = item[1]
                f.write('{},{},{},{},{}\n'.format(card_c, trans_c,
                        visa_date_string(date), master_date_string(date),
                        get_mvb(card_c, trans_c)))
