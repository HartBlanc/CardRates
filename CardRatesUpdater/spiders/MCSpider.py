# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings as settings
from ..items import updaterItem
import csv
import json
import scrapy
from pathlib import Path
from datetime import datetime
import requests

std_date_fmt = settings().get()('STD_DATE_FMT')


class MCSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'MCSpider'
    provider = 'Mastercard'
    allowed_domains = ['mastercard.co.uk']

    url = 'https://www.mastercard.co.uk/'
    curr_url = url + 'settlement/currencyrate/settlement-currencies'
    support_url = url + 'en-gb/consumers/get-support/convert-currency.html'
    rate_url = url + "settlement/currencyrate/{}/conversion-rate"

    date_fmt = '%Y-%m-%d'

    err_msgs = {'104': None, '101': None '500': None '401': None '400': None,
                None: "conversion rate too small"}

    rate_params = {'fxDate': None, 'transCurr': None, 'crdhldBillCurr': None,
                   'bankFee': '0.0', 'transAmt': '1'}

    def __init__(self, data=None, number=None, *args, **kwargs):
        super(MCSpider, self).__init__(*args, **kwargs)
        self.number = number
        self.data = csv.reader(Path(f'input/{number}.csv').open())

    # a generator function for the correct initial requests
    # (all codes and dates to correct formatted urls)
    def start_requests(self):
        for card_c, trans_c, date in self.data:
            date = self.fmt_date(date)
            item = updaterItem(card_c, trans_c, date)

            params = dict(self.rate_params)
            params['crdhldBillCurr'] = card_c
            params['transCurr'] = trans_c
            params['fxDate'] = date

            param_string = ''.join([f'{k}={v};' for k, v in params.items()])[:-1]

            yield (scrapy.Request(
                url=self.rate_url.format(param_string),
                headers={'referer': MC.url + MC.support_url},
                meta=dict(item=item)))

    def parse(self, response):
        item = response.meta['item']
        depth = response.meta['depth']

        jresponse = json.loads(response.body_as_unicode())
        if 'errorCode' in jresponse['data']:
            errcd = jresponse['data']['errorCode']
            print('Dropping Item:', item, 'Error msg:' self.err_msgs[errcd])
            item['rate'] = None

        else:
            item['rate'] = jresponse['data']['conversionRate']

        wanted = {'card_c': None, 'trans_c': None, 'date': None, 'rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)
        return item

    @classmethod
    def fetch_avail_currs(self):
        # return dict()
        r = requests.get(self.curr_api, headers={"referer": self.referer})
        assert r.ok, "Request failed - ip may be blocked"

        codes = {x['alphaCd']: x['currNam'].strip()
                 for x in r.json()['data']['currencies']}
        assert len(codes) != 0, 'No currencies found, check url and selector'

        return codes

    @classmethod
    def fmt_date(self, std_date):
        return (datetime.strptime(std_date, std_date_fmt)
                        .strftime(self.date_fmt))
