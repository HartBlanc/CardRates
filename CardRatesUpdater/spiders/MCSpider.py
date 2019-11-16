from ..items import updaterItem
import csv
import json
import scrapy
import time
import urllib
from db_orm import MC

def get_m_rate(response):
    # handles errors and returns the m_rate from json
    # see errors text document for more info
    jsonresponse = json.loads(response.body_as_unicode())
    data = jsonresponse['data']
    if 'errorCode' in data:
        if data['errorCode'] in ('104', '114'):
            return None
        elif data['errorCode'] in ('500', '401', '400'):
            print("Server having technical problems")
            return 'retry'
        else:
            print("conversion rate too small")
            return None
    else:
        return data['conversionRate']


# UpdaterSpider
class UpdaterSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'MCSpider'
    allowed_domains = [MC.domain]

    def __init__(self, data=None, number=None, *args, **kwargs):
        super(UpdaterSpider, self).__init__(*args, **kwargs)
        self.number = number
        self.data = csv.reader(open('input/{}.csv'.format(number)))

    # a generator function for the correct initial requests
    # (all codes and dates to correct formatted urls)
    def start_requests(self):
        for card_c, trans_c, date in self.data:
            yield (scrapy.Request(
                         url=MC.rate_url(date, trans_c, card_c),
                         headers={'referer': MC.url + MC.support_url},
                         meta=dict(item=item)))

    def parse(self, response):
        item = response.meta['item']
        depth = response.meta['depth']

        # contains rate or notifys error
        option = get_m_rate(response)

        # error handling
        if option == 'retry':
            # retry 8 times, wait 5 seconds between, handles server issues
            if depth < 8:
                print('Depth: ', depth, 'Item:', item)
                yield response.request.replace(dont_filter=True)
            else:
                item['rate'] = None
        else:
            item['rate'] = option

        wanted = {'card_c': None, 'trans_c': None, 'master_date': None,
                  'V_Rate': None, 'M_Rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)
        yield item