'''
This module is responsible for initial creation of the database
'''

import sqlite3
import requests
from lxml import html
import datetime


def get_master_currs_and_codes():
    # creates a set of all codes that mastercard provides rates for
    r = requests.get(MASTERCARD + SETTLEMENT,
                     headers={"referer": MASTERCARD + SUPPORT})
    JSON = r.json()
    codes = {x['alphaCd']: x['currNam'].strip()
             for x in JSON['data']['currencies']}
    assert len(codes) != 0
    return codes


def get_all_currs_and_codes():
    master_currs_and_codes = get_master_currs_and_codes()
    visa_currs_and_codes = get_visa_currs_and_codes()
    master_set = set(master_currs_and_codes.keys())
    visa_set = set(visa_currs_and_codes.keys())

    visa_only = visa_set - master_set
    all_currs_and_codes = {**master_currs_and_codes,
                           **{code: visa_currs_and_codes[code]
                              for code in visa_only}}
    return sorted(all_currs_and_codes.items())


def createTables(cur):

    cur.execute('''CREATE TABLE currency_codes (
    curr_id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    alpha_code TEXT NOT NULL UNIQUE
    );''')

    cur.execute('''CREATE TABLE dates (
    date_id INTEGER NOT NULL PRIMARY KEY,
    date TEXT NOT NULL UNIQUE
    );''')

    cur.execture('''CREATE TABLE providers
    provider_id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
    );''')

    cur.execute('''CREATE TABLE rates (
    rate_id INTEGER NOT NULL PRIMARY KEY,
    card_id INTEGER NOT NULL,
    trans_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    rate REAL,
    UNIQUE(card_id, trans_id, date_id, provider_id)
    );''')


if __name__ == '__main__':
    con = sqlite3.connect('CardRates.db')
    tables = ["Rates", "sates", "currency_codes"]
    createTables(con)
    sql = 'INSERT into Currency_codes (alphaCd, name) Values (?, ?)'
    con.executemany(sql, get_all_currs_and_codes())
    numdays = 2000
    date_gen = ((FIRST_DATE + datetime.timedelta(days=x), )
                for x in range(0, numdays))
    con.executemany('INSERT into Dates (date) Values (?)', date_gen)
    con.commit()
    con.close()
