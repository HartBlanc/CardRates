# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings as settings
import scrapy

from db_orm import Rate, Provider, CurrencyCode

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from datetime import datetime

std_date_fmt = settings().get('STD_DATE_FMT')


class CardRatesUpdaterPipeline(object):

    def __init__(self):
        self.setupDBCon()
        self.commit_count = 0

    def open_spider(self, spider):
        provider = spider.provider
        self.provider_id = (self.session.query(Provider.id)
                                        .filter(Provider.name == provider))

    def strpdate(self, std_date):
        return datetime.strptime(std_date, std_date_fmt).date()

    # methods to ensure database saves when spider closes
    @classmethod
    def from_crawler(cls, crawler):
        temp = cls()
        crawler.signals.connect(
            temp.spider_closed, signal=scrapy.signals.spider_closed)
        return temp

    # methods to ensure database saves when spider closes
    def spider_closed(self, reason):
        print("Committing changes")
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def setup_db_con(self):
        engine = create_engine(settings().get("CONNECTION_STRING"))
        session = sessionmaker(bind=engine)
        self.session = session()

    def process_item(self, item, spider):
        self.store_in_db(item)
        return item

    def store_in_db(self, item):
        self.session.add(Rate(card_code=item['card_c'],
                              trans_code=item['trans_c'],
                              date=self.strpdate(item['date']),
                              provider_id=self.provider_id,
                              rate=item['rate']))

        # Limit writing to disk to every 100 rows
        if self.commit_count == 99:
            self.session.commit()

        self.commit_count = (self.commit_count + 1) % 100

    def __del__(self):
        self.session.close()

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
