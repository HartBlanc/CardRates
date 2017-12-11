import sqlite3
import csv
import glob
import os
import shutil
from pre import get_code_list, day_calculator
from datetime import datetime


def master_date_to_day(master_string):
    master_date = datetime.strptime(master_string, '%Y-%m-%d').date()
    return day_calculator(master_date)


def clean_up(l):
    # replace codes with code_ids
    l[0] = all_codes.index(l[0]) + 1
    l[1] = all_codes.index(l[1]) + 1
    l[2] = master_date_to_day(l[2])
    # replace empty strings with null values
    if l[3] == '':
        l[3] = None
    if l[4] == '':
        l[4] = None
    return l


def do_directory(dirname, db):
    # get all csv files in the directory
    for filename in glob.glob(os.path.join(dirname, '*.csv')):
        do_file(filename, db)


def do_file(filename, db):
    # get csv file, delete headings, clean up, insert to database and commit
    with open(filename) as f:
        print(filename)
        with db:
            data = list(csv.reader(f))
            print(len(data))
            if len(data) == 0:
                return
            del data[0]
            sql = 'insert into Rates values (?, ?, ?, ?, ?)'
            db.executemany(sql, map(clean_up, data))
    os.remove(filename)


if __name__ == '__main__':
    con = sqlite3.connect('CardRates.db')
    all_codes = get_code_list(con.cursor())
    do_directory('output', con)
    print("Cleaning Database")
    con.execute('VACUUM')
    con.close()
    shutil.rmtree('input')
    shutil.rmtree('output')
