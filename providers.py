
import requests
from lxml import html

# move to config file
VISA_URL = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
VISA_XPATH = '//*[@id="fromCurr"]/option'
MC_URL = 'https://www.mastercard.co.uk/'
MC_SETTLEMENT = 'settlement/currencyrate/settlement-currencies'
MC_SUPPORT = 'en-gb/consumers/get-support/convert-currency.html'


class Provider:
    '''
    The Provider class is responsible for maintaining:
        * The set of available currencies
        * URLs associated with the provider
        * Selectors associated with the provider
        * Request headers
        * Request form data
    '''

    def __init__(self, url):

        self.url = url
        self.avail_currs = self.fetch_avail_currs

    def fetch_avail_currs(self):
        '''
        creates a set of all codes that the provider provides rates for

        returns: {alphacd: name}

        alphacd : str - three letter ISO 4217 style currency code
        name : str - vendor provided name of currency
        '''

        pass


class Visa(Provider):

    def __init__(self, url, xpath):

        self.xpath = xpath
        super(Y, self).__init__(url)

    def fetch_avail_currs():

        page = requests.get(self.url)
        tree = html.fromstring(page.content)
        options = tree.xpath(self.xpath)
        codes = {o.attrib['value']: o.text[:-6].upper() for o in options
                 if len(o.attrib['value']) == 3}
        assert len(codes) != 0, 'No currencies found, check url and selector'
        return codes


class MC(Provider):

    def __init__(self, url, referer, api):
        self.referer = url + referer
        self.api = url + api
        super(Y, self).__init__(url)

    def fetch_avail_currs():

        r = requests.get(self.api, headers={"referer": self.referer})
        codes = {x['alphaCd']: x['currNam'].strip()
                 for x in r.json()['data']['currencies']}
        assert len(codes) != 0, 'No currencies found, check url and selector'
        return codes
