# -*- coding: utf-8 -*-
import sqlite3
import scrapy
from random import randint
from db_orm import Rate, Provider, CurrencyCode
import datetime
from sqlalchemy import create_engine
from scrapy.utils.project import get_project_settings
from sqlalchemy.orm import sessionmaker


class CardRatesUpdaterPipeline(object):

    def __init__(self):
        self.setupDBCon()
        self.cd_to_id = self.alphaCd_to_id()

    def open_spider(self, spider):
        provider = spider.name.replace('Spider', '')
        self.provider_id = (self.session.query(Provider.id)
                                        .filter(Provider.name == provider))
        self.date_fmt = spider.date_fmt

    def alphaCd_to_id(self):
        q = self.session.query(CurrencyCode.alpha_code, CurrencyCode.id)
        return {ac: id for ac, id in q}

    def date_to_id(self, date):
        d = datetime.datetime.strptime(date, self.date_fmt).date()
        return (d - datetime.date(2016, 10, 14)).days + 1

    # methods to ensure database saves when spider closes
    @classmethod
    def from_crawler(cls, crawler):
        temp = cls()
        crawler.signals.connect(
            temp.spider_closed, signal=scrapy.signals.spider_closed)
        return temp

    # methods to ensure database saves when spider closes
    def spider_closed(self, reason):
        print("Commiting changes")
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def setupDBCon(self):
        engine = create_engine(get_project_settings().get("CONNECTION_STRING"))
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def process_item(self, item, spider):
        self.storeInDb(item)
        return item

    def storeInDb(self, item):
        self.session.add(Rate(card_id=self.cd_to_id[item['card_c']],
                              trans_id=self.cd_to_id[item['trans_c']],
                              date_id=self.date_to_id(item['date']),
                              provider_id=self.provider_id,
                              rate=item['rate']))
        # randomness means that database isn't saving excessively
        if randint(1, 100) == 1:
            self.session.commit()

    def __del__(self):
        self.session.close()

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
