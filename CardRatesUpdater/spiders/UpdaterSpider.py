from ..items import updaterItem
import csv
import json
import scrapy
import time

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


RATE_URL = ('settlement/currencyrate/'
            'fxDate={};transCurr={};crdhldBillCurr={};bankFee=0.00;transAmt=1'
            '/conversion-rate')
MASTERCARD = 'https://www.mastercard.co.uk/'
REFERER = 'en-gb/consumers/get-support/convert-currency.html'
VISA_URL = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
VISA_XPATH = '//p[@class="currency-convertion-result h2"]/strong[1]/text()'


# large text file, open and close
with open('visa_form_data.txt') as f:
    VISA_BASE_FORM = f.read()


# UpdaterSpider
class UpdaterSpider(scrapy.Spider):
    # Need name to call spider from terminal
    name = 'UpdaterSpider'
    allowed_domains = ['mastercard.co.uk', 'visa.co.uk']

    def __init__(self, data=None, number=None, *args, **kwargs):
        super(UpdaterSpider, self).__init__(*args, **kwargs)
        self.number = number
        self.data = csv.reader(open('input/{}.csv'.format(number)))

    def m_request(self, item):
        # A function to request the mastercard url and send to next call
        # decides where to go next: parse or get visa rate for same date?
        if item['mvb'] == 'm':
            next_function = self.parse
        else:
            next_function = self.parse_master
        # sends formatted request to mastercard
        # passes on item through meta
        return (scrapy
                .Request(callback=next_function,
                         url=MASTERCARD + RATE_URL.format(item['master_date'],
                                                          item['trans_c'],
                                                          item['card_c']),
                         headers={'referer': MASTERCARD + REFERER},
                         meta=dict(item=item)))

    def v_request(self, item):

        # sends formatted request to visa and continues to the parse function
        # passes on item through meta
        params = f"?amount=1&fee=0.0&exchangedate={item['visa_date']}&fromCurr={item['card_c']}&toCurr={item['trans_c']}&submitButton=Calculate+exchange+rate"
        return scrapy.Request(callback=self.parse, url=VISA_URL+params, meta=dict(item=item))
        return scrapy.FormRequest(callback=self.parse, url=VISA_URL+params,
                                  headers=ER_HEAD, formdata=post,
                                  meta=dict(item=item))

    # a generator function for the correct initial requests
    # (all codes and dates to correct formatted urls)
    def start_requests(self):
            for row in self.data:
                item = updaterItem()
                item['card_c'] = row[0]
                item['trans_c'] = row[1]
                item['visa_date'] = row[2]
                item['master_date'] = row[3]
                item['mvb'] = row[4]
                if item['mvb'] == 'v':
                    yield self.v_request(item)
                else:
                    # keeps a record of how many times the mastercard url has
                    # been requested for error handling
                    item['depth'] = 1
                    yield self.m_request(item)

    def parse_master(self, response):
        item = response.meta['item']
        # contains rate or notifys error
        option = get_m_rate(response)
        # error handling
        if option == 'retry':
            # retry 8 times, wait 5 seconds between, handles server issues
            if item['depth'] < 8:
                print(1, item)
                item['depth'] += 1
                time.sleep(5)
                yield self.m_request(item)
            else:
                item['M_Rate'] = None
        else:
            item['M_Rate'] = option
        yield self.v_request(item)

    def parse(self, response):
        item = response.meta['item']
        if item['mvb'] == 'm':
            option = get_m_rate(response)
            if option == 'retry':
                if item['depth'] < 8:
                    print(2, item)
                    item['depth'] += 1
                    time.sleep(5)
                    yield self.m_request(item)
                else:
                    item['M_Rate'] = None
            else:
                item['M_Rate'] = option
                item['V_Rate'] = None
        # extract visa rate using xpath
        else:
            # inspect_response(response, self)
            item['V_Rate'] = response.xpath(VISA_XPATH).get().split()[0].replace(',','')

            if item['mvb'] == 'v':
                item['M_Rate'] = None
        # pass item onto pipeline
        wanted = {'card_c': None, 'trans_c': None, 'master_date': None,
                  'V_Rate': None, 'M_Rate': None}
        unwanted_keys = set(item.keys()) - set(wanted.keys())
        for unwanted_key in unwanted_keys:
            item.pop(unwanted_key, None)
        yield item
