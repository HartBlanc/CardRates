# -*- coding: utf-8 -*-
import sqlite3
import scrapy
from random import randint


# DEPRECEATED

def get_code_list():
    # codes[i]+1 are the code ids
    con = sqlite3.connect('CardRates.sqlite')
    cur = con.cursor()
    cur.execute('SELECT code FROM Currency_Codes')
    code_tuples = cur.fetchall()
    # fetchall returns e.g. [(USD,)...]
    codes = [x[0] for x in code_tuples]
    con.close()
    print("I got the code list!")
    return codes


all_codes = get_code_list()
print(all_codes)


class CardratesupdaterPipeline(object):

    def __init__(self):
        self.setupDBCon()

    # methods to ensure database saves when spider closes
    @classmethod
    def from_crawler(cls, crawler):
        temp = cls()
        crawler.signals.connect(
            temp.spider_closed, signal=scrapy.signals.spider_closed)
        return temp

    # methods to ensure database saves when spider closes
    def spider_closed(self, reason):
        print("saving to DB")
        self.con.commit()

    def setupDBCon(self):
        self.con = sqlite3.connect('CardRates.sqlite')
        self.cur = self.con.cursor()
        print("DB is good to go!")

    def process_item(self, item, spider):
        self.storeInDb(item)
        return item

    def storeInDb(self, item):
        self.cur.execute('''INSERT OR REPLACE INTO Rates(card_id, trans_id, date_id, mastercard, visa)
        VALUES( ?, ?, ?, ?, ?)''', (all_codes.index(item['card_c']) + 1, all_codes.index(item['trans_c']) + 1, item['date_id'], item['rate']))
        # randomnes means that database isn't saving after every iteration
        # unneccesarily
        if randint(1, 100) >= 99:
            self.con.commit()

    def closeDB(self):
        self.con.close()

    def __del__(self):
        self.closeDB()

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
