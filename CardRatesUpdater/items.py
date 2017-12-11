# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class updaterItem(scrapy.Item):
    card_c = scrapy.Field()
    trans_c = scrapy.Field()
    visa_date = scrapy.Field()
    master_date = scrapy.Field()
    mvb = scrapy.Field()
    M_Rate = scrapy.Field()
    V_Rate = scrapy.Field()
    depth = scrapy.Field()
