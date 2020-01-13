# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings as settings
from ..items import UpdaterItem
import scrapy

from datetime import datetime

from pathlib import Path
import csv

from lxml import html
import requests
import urllib

std_date_fmt = settings().get('STD_DATE_FMT')


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

    def __init__(self, data=None, inpath=None, *args, **kwargs):
        super(VisaSpider, self).__init__(*args, **kwargs)
        self.data = csv.reader(Path(inpath).open())

    def start_requests(self):
        for card_c, trans_c, date in self.data:
            item = UpdaterItem(card_c, trans_c, date)

            params = dict(self.rate_params)
            params['date'] = self.fmt_date(date)
            params['fromCurr'] = card_c
            params['toCurr'] = trans_c
            url = f'{self.url}?{urllib.parse.urlencode(params)}'

            yield scrapy.Request(url=url, meta=dict(item=item))

    def parse(self, response):
        item = response.meta['item']
        try:
            item['rate'] = (response.xpath(self.rate_xpath)
                                    .get()
                                    .split()[0]
                                    .replace(',', ''))
        except AttributeError:
            item['rate'] = None

        wanted = {'card_c': None, 'trans_c': None, 'date': None, 'rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)

    @classmethod
    def fetch_avail_currs(self):
        page = requests.get(self.url)
        r = requests.get(self.url)
        tree = html.fromstring(page.content)
        assert r.ok, "Request failed - ip may be blocked"
        tree = html.fromstring(r.content)

        options = tree.xpath(self.curr_xpath)
        codes = {o.attrib['value']: o.text[:-6].upper() for o in options
                 if len(o.attrib['value']) == 3}

    @classmethod
    def fmt_date(self, std_date):
        return (datetime.strptime(std_date, std_date_fmt)
                        .strftime(self.date_fmt))
