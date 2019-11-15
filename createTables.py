import sqlite3
import requests
from lxml import html
import datetime
from pre import drop_tables, MASTERCARD, SETTLEMENT, SUPPORT, FIRST_DATE


def get_visa_currs_and_codes():
    # creates a set of all codes that visa provides rates for
    visa_url = 'https://www.visaeurope.com/making-payments/exchange-rates'
    page = requests.get(visa_url)
    tree = html.fromstring(page.content)
    cur_xpath = ("//select[@name="
                 "'ctl00$ctl00$MainContent$MainContent$ctl00$ddlCardCurrency']"
                 "/option")
    options = tree.xpath(cur_xpath)
    codes = {o.attrib['value']: o.text[6:].upper()
             for o in options
             if len(o.attrib['value']) == 3}
    return codes


def get_master_currs_and_codes():
    # creates a set of all codes that mastercard provides rates for
    r = requests.get(MASTERCARD + SETTLEMENT,
                     headers={"referer": MASTERCARD + SUPPORT})
    JSON = r.json()
    codes = list()
    codes = {x['alphaCd']: x['currNam'].strip()
             for x in JSON['data']['currencies']}
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

    cur.execute('''CREATE TABLE Currency_Codes (
    currency text NOT NULL UNIQUE,
    code text NOT NULL UNIQUE
    );''')

    cur.execute('''CREATE TABLE Rates (
     card_id INTEGER NOT NULL,
     trans_id INTEGER NOT NULL,
     date_id INTEGER NOT NULL,
     mastercard REAL,
     visa REAL,
     UNIQUE(card_id, trans_id, date_id)
     );''')

    cur.execute('''CREATE TABLE Dates (
     date TEXT NOT NULL UNIQUE
     );''')


if __name__ == '__main__':
    con = sqlite3.connect('CardRates.db')
    tables = ["Rates", "Dates", "Currency_codes"]
    drop_tables(con, tables)
    createTables(con)
    sql = 'INSERT into Currency_codes (code, currency) Values (?, ?)'
    con.executemany(sql, get_all_currs_and_codes())
    numdays = 1000
    date_gen = ((FIRST_DATE + datetime.timedelta(days=x), )
                for x in range(0, numdays))
    con.executemany('INSERT into Dates (date) Values (?)', date_gen)
    con.commit()
    con.close()
