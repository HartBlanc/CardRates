# -*- coding: utf-8 -*-
from ..items import UpdaterItem
import scrapy

from datetime import datetime

from pathlib import Path
import csv

from lxml import html
import requests
import urllib

from db.client import std_date_fmt


class VisaSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'VisaSpider'
    allowed_domains = ['visa.co.uk']
    provider = 'Visa'

    date_fmt = '%m/%d/%Y'
    url = ('https://www.visa.co.uk/'
           'support/consumer/travel-support/'
           'exchange-rate-calculator.html')

    curr_xpath = '//*[@id="fromCurr"]/option'
    rate_xpath = '//p[@class="currency-convertion-result h2"]/strong[1]/text()'

    rate_params = {'amount': '1', 'fee': '0.0', 'exchangedate': None,
                   'fromCurr': None, 'toCurr': None,
                   'submitButton': 'Calculate exchange rate'}

    def __init__(self, in_path=None, *args, **kwargs):
        super(VisaSpider, self).__init__(*args, **kwargs)
        self.in_path = Path(in_path)

    def start_requests(self):
        with self.in_path.open() as data:
            for card_c, trans_c, date in csv.reader(data):
                item = UpdaterItem(card_c, trans_c, date)

                params = dict(self.rate_params)
                params['exchangedate'] = self.fmt_date(date)
                params['fromCurr'] = card_c
                params['toCurr'] = trans_c
                # noinspection PyUnresolvedReferences
                url = f'{self.url}?{urllib.parse.urlencode(params)}'

                yield scrapy.Request(url=url, meta=dict(item=item))

    def parse(self, response):
        item = response.meta['item']

        item['rate'] = response.xpath(self.rate_xpath)\
                               .get()\
                               .split()[0]\
                               .replace(',', '')

        wanted = {'card_c': None, 'trans_c': None, 'date': None, 'rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)

        return item

    @classmethod
    def fetch_avail_currs(cls):
        r = requests.get(cls.url)
        assert r.ok, "Request failed - ip may be blocked"
        tree = html.fromstring(r.content)

        options = tree.xpath(cls.curr_xpath)
        codes = {o.attrib['value']: o.text[:-6].upper() for o in options
                 if len(o.attrib['value']) == 3}

        return codes

    @classmethod
    def fmt_date(cls, std_date):
        return (datetime.strptime(std_date, std_date_fmt)
                        .strftime(cls.date_fmt))
