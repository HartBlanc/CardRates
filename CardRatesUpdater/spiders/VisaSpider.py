from ..items import updaterItem
import csv
import scrapy
from scrapy.shell import inspect_response
import urllib
from db_orm import Visa


class VisaSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'VisaSpider'
    allowed_domains = [Visa.domain]

    def __init__(self, data=None, number=None, *args, **kwargs):
        super(VisaSpider, self).__init__(*args, **kwargs)
        self.number = number
        self.data = csv.reader(open('input/{}.csv'.format(number)))

    def start_requests(self):
        for card_c, trans_c, date in self.data:
            yield self.v_request(updaterItem(card_c, trans_c, date))

    def v_request(self, item):

        # sends formatted request to visa and continues to the parse function
        # passes on item through meta
        params = dict(Visa.rate_params)
        params['date'] = item['date']
        params['fromCurr'] = item['card_c']
        params['toCurr'] = item['trans_c']
        url = f'{Visa.url}?{urllib.parse.urlencode(params)}'

        return scrapy.Request(callback=self.parse, url=url, meta=dict(item=item))

    def parse(self, response):
        item = response.meta['item']
        try:
            item['rate'] = (response.xpath(Visa.rate_xpath).get()
                                    .split()[0].replace(',', ''))
        except AttributeError:
            item['rate'] = None

        wanted = {'card_c': None, 'trans_c': None, 'date': None, 'rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)
        yield item
