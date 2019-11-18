from ..items import updaterItem
import csv
import scrapy
from db_orm import Visa
from pathlib import Path


class VisaSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'VisaSpider'
    date_fmt = '%m/%d/%Y'
    allowed_domains = [Visa.domain]

    def __init__(self, data=None, number=None, *args, **kwargs):
        super(VisaSpider, self).__init__(*args, **kwargs)
        self.number = number
        self.data = csv.reader(Path(f'input/{number}.csv').open())

    def start_requests(self):
        for card_c, trans_c, date in self.data:
            item = updaterItem(card_c, trans_c, date)
            url = Visa.rate_url_p(date, trans_c, card_c)
            yield scrapy.Request(callback=self.parse, url=url, meta=dict(item=item))

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
        return item
