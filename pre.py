from sys import argv
import sqlite3
import datetime
import pytz
import requests
import os
from lxml import html
from itertools import product

'''
#TO-DO
* Do I need to write to csv?
* Can I use multiprocessing if I do need to?
* Refactoring required
* Add missing currencies
'''

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
    return date.strftime('%m/%d/%Y')


def find_visa_set():
    # creates a set of all codes that visa provides rates for
    m_rate_url = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
    page = requests.get(m_rate_url)
    tree = html.fromstring(page.content)
    cur_xpath = '//*[@id="fromCurr"]/option/@value'
    options = tree.xpath(cur_xpath)
    codes = {o for o in options if len(o) == 3}
    assert len(codes) > 0
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
    print("generating all combos")
    return {(x, y, z) for x, y, z in product(l1, l1, l2) if x != y}


def find_missing_combos(cur, vnm, mnv):
    print("finding missing combos")

    cur.execute('SELECT * FROM Rates')
    not_missing = {(card_id, trans_id, date_id) for
                    card_id, trans_id, date_id, m, v in cur.fetchall()
                    if m is not None and v is not None
                    or v is not  None and card_id in mnv
                    or m is not None and card_id in vnm}

    all_combos = create_all_combos(cur, range(1, len(all_db_codes) + 1),
                                range(TODAY - 363, TODAY + 1)
                                )

    missing = all_combos - not_missing
    print(len(missing))
    return missing


def fetch_data(cur, missing):
    cur_list = cur.execute('SELECT code from Currency_Codes')

    cur_dict = {i+1:code[0] for i, code in enumerate(cur_list)}

    return [(cur_dict[card_id], cur_dict[trans_id], date_id) for card_id, trans_id, date_id in missing]



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
    create_all_combos(cur, range(1, len(all_db_codes) + 1),
                      range(TODAY - 363, TODAY + 1)
                      )
    missing = find_missing_combos(cur, index_tuple(list(all_db_codes), visa_only),
                                  index_tuple(list(all_db_codes), master_only)
                                 )
    data = fetch_data(cur, missing)
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
                f.write(f'{card_c},{trans_c},{visa_date_string(date)},{master_date_string(date)},{get_mvb(card_c, trans_c)}\n')
