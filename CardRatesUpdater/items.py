# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class updaterItem(scrapy.Item):
    card_c = scrapy.Field()
    trans_c = scrapy.Field()
    date = scrapy.Field()
    rate = scrapy.Field()

    def __init__(self, card_c, trans_c, date, *args, **kwargs):
        super(updaterItem, self).__init__(*args, **kwargs)
        self['card_c'] = card_c
        self.['trans_c'] = trans_c
        self.['date'] = date
