from sys import argv
import sqlite3
import datetime
import requests
import os
from lxml import html
from itertools import product
from utils import VISA_URL, MC_URL, MC_SETTLEMENT, MC_SUPPORT, FIRST_DATE

'''
#TO-DO
* Do I need to write to csv?
* Can I use multiprocessing if I do need to?
* Refactoring required
* Add functionality to update missing currencies
* Update paths to use pathlib 
* caching on mvb?
'''

def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]

def date_id_to_date(date_id):
    # converts a date_id into a date
    return FIRST_DATE + datetime.timedelta(date_id - 1)

def get_db_alphasCds(cur):
    # gets the list of all codes from the database
    # codes[i]+1 are the code ids
    cur.execute('SELECT code FROM Currency_Codes')
    cd_tuples = cur.fetchall()
    return {x[0] for x in cd_tuples}

def create_all_combos(cur, l1, l2):
    # all combinations where the currencies aren't the same
    return {(x, y, z) for x, y, z in product(l1, l1, l2) if x != y}

def find_missing_combos(cur, vnm, mnv):

    cur.execute('SELECT * FROM Rates')
    not_missing = {(card_id, trans_id, date_id) for
                    card_id, trans_id, date_id, m, v in cur.fetchall()
                    if m is not None and v is not None
                    or v is not  None and card_id in mnv
                    or m is not None and card_id in vnm}

    all_combos = create_all_combos(cur, range(1, len(db_alphaCds) + 1),
                                   range(TODAY - 363, TODAY + 1)
                                  )

    missing = all_combos - not_missing
    print(len(missing))
    return missing

def alphaCds_to_ids(cur, missing):
    cur_list = cur.execute('SELECT code from Currency_Codes')

    cur_dict = {i+1:code[0] for i, code in enumerate(cur_list)}

    return [(cur_dict[card_id], cur_dict[trans_id], date_id) for card_id, trans_id, date_id in missing]

def get_mvb(card_c, trans_c):
    # Is the currency supplied just by mastercard, just visa or both?
    # stops unnessecary requests
    # the empty set returns false
    if {card_c, trans_c} & mc_only:
        return "m"
    elif {card_c, trans_c} & visa_only:
        return "v"
    else:
        return "b"

def index_tuple(l1, l2):
    return tuple(map(lambda x: l1.index(x) + 1, l2))



if __name__ == '__main__':
    no_of_chunks = int(argv[1])
    con = sqlite3.connect('CardRates.db')
    cur = con.cursor()
    db_alphaCds = get_db_alphasCds(cur)
    mc_alphaCds = fetch_mc_alphaCds()
    visa_alphaCds = fetch_visa_alphaCds()
    visa_only = visa_alphaCds - mc_alphaCds
    mc_only = mc_alphaCds - visa_alphaCds
    all_online_codes = mc_alphaCds | visa_alphaCds
    missing_codes = all_online_codes - db_alphaCds
    print("Visa only:", visa_only)
    print("Master only:", mc_only)
    print("Missing from DB:", missing_codes)
    create_all_combos(cur, range(1, len(db_alphaCds) + 1),
                      range(TODAY - 363, TODAY + 1)
                      )
    missing = find_missing_combos(cur, index_tuple(list(db_alphaCds), visa_only),
                                  index_tuple(list(db_alphaCds), mc_only)
                                 )
    data = alphaCds_to_ids(cur, missing)
    con.close()
    chunked = chunkify(data, no_of_chunks)
    os.mkdir('input')
    os.mkdir('output')
    print(len(chunked))
    for i in range(0, N):
        print(len(chunked[i]))
    for (i, chunk) in enumerate(chunked):
        with open('input/' + str(i) + '.csv', 'w') as f:
            for item in chunk:
                date = date_id_to_date(item[2])
                card_c = item[0]
                trans_c = item[1]
                f.write(f'{card_c},{trans_c},{visa_date_fmt(date)},{mc_date_fmt(date)},{get_mvb(card_c, trans_c)}\n')
