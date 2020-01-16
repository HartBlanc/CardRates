# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings as settings
from ..items import UpdaterItem
import scrapy

from datetime import datetime

from pathlib import Path
import csv

import requests
import json

std_date_fmt = settings().get('STD_DATE_FMT')


class MCSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'MCSpider'
    provider = 'Mastercard'
    allowed_domains = ['mastercard.co.uk']

    url = 'https://www.mastercard.co.uk/'
    curr_url = url + 'settlement/currencyrate/settlement-currencies'
    support_url = url + 'en-gb/consumers/get-support/convert-currency.html'
    rate_url = url + 'settlement/currencyrate/{}/conversion-rate'
    date_fmt = '%Y-%m-%d'
    # todo should this add null to database?
    # err_msgs to be identified.
    # err_msgs = {'101': None,
    #             '104': None,
    #             '114': "Not Found , Conversion rate is not available for this currency pair."
    #             '400': None,
    #             '401': None,
    #             '500': None,
    #             }

    rate_params = {'fxDate': None, 'transCurr': None, 'crdhldBillCurr': None,
                   'bankFee': '0.0', 'transAmt': '1'}

    def __init__(self, in_path=None, *args, **kwargs):
        super(MCSpider, self).__init__(*args, **kwargs)
        self.in_path = Path(in_path)

    # a generator function for initial requests
    # (formatted urls from currency alphaCds and dates)
    def start_requests(self):
        with self.in_path.open() as data:
            for card_c, trans_c, date in csv.reader(data):
                item = UpdaterItem(card_c, trans_c, date)

                params = dict(self.rate_params)
                params['crdhldBillCurr'] = card_c
                params['transCurr'] = trans_c
                params['fxDate'] = self.fmt_date(date)

                param_string = ''.join(f'{k}={v};' for k, v in params.items())[:-1]

                yield (scrapy.Request(
                    url=self.rate_url.format(param_string),
                    headers={'referer': self.support_url},
                    meta=dict(item=item)))

    def parse(self, response):
        item = response.meta['item']

        j_response = json.loads(response.body_as_unicode())
        if 'errorCode' in j_response['data']:
            # err_cd = j_response['data']['errorCode']
            print(f"Dropping Item: {item}, Error msg: \"{j_response['data'].get('errorMessage')}\"")
            return
        else:
            item['rate'] = j_response['data']['conversionRate']

        wanted = {'card_c': None, 'trans_c': None, 'date': None, 'rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)
        return item

    @classmethod
    def fetch_avail_currs(cls):
        r = requests.get(cls.curr_url, headers={"referer": cls.support_url})

        assert r.ok, "Request failed - ip may be blocked"

        codes = {x['alphaCd']: x['currNam'].strip()
                 for x in r.json()['data']['currencies']}

        assert len(codes) != 0, "No currencies found, check url and selector"

        return codes

    @classmethod
    def fmt_date(cls, std_date):
        return (datetime.strptime(std_date, std_date_fmt)
                .strftime(cls.date_fmt))
