# -*- coding: utf-8 -*-
import scrapy

from db_orm import Rate, Provider
from db_client import DbClient, strpdate


class CardRatesUpdaterPipeline(object):

    def __init__(self):
        self.provider_id = None
        self.client = DbClient()
        self.session = self.client.session_maker()
        self.commit_count = 0

    def open_spider(self, spider):
        provider = spider.provider
        self.provider_id = (self.session
                                .query(Provider.id)
                                .filter(Provider.name == provider))

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

    def process_item(self, item, spider):
        self.session.add(Rate(card_code=item['card_c'],
                              trans_code=item['trans_c'],
                              date=strpdate(item['date']),
                              provider_id=self.provider_id,
                              rate=item['rate']))

        # Limit writing to disk to every 100 rows
        if self.commit_count == 99:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise

        self.commit_count = (self.commit_count + 1) % 100

        return item

    def __del__(self):
        self.session.close()

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
