from sqlalchemy import (Column, Integer, String, Float, UniqueConstraint,
                        ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from lxml import html
import requests
import datetime
import urllib

Base = declarative_base()


class Provider(Base):
    __tablename__ = 'providers'

    datefmt = None

    # assumed that sqlalchemy won't allow null for pk
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __init__(self, *args, **kwargs):
        super(Provider, self).__init__(*args, **kwargs)

        self.avail_currs = self.fetch_avail_currs()

    def fetch_avail_currs(self):
        '''
        creates a set of all codes that the provider provides rates for

        returns: {alphacd: name}

        alphacd : str - three letter ISO 4217 style currency code
        name : str - vendor provided name of currency
        '''

        pass

    def date_string(self, date):
        '''
        Uses a datetime.date object and the date_fmt attrib
        to produce a date str compatabile with apis
        '''

        return date.strftime(self.date_fmt)

    def __repr__(self):
        return f"<Provider(name='{self.name}')>"


class Visa(Provider):

    domain = 'visa.co.uk'
    url = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
    curr_xpath = '//*[@id="fromCurr"]/option'
    rate_xpath = '//p[@class="currency-convertion-result h2"]/strong[1]/text()'
    date_fmt = '%m/%d/%Y'
    # name = "Visa"
    rate_params = {'amount': '1', 'fee': '0.0', 'exchangedate': None,
                   'fromCurr': None, 'toCurr': None,
                   'submitButton': 'Calculate exchange rate'}

    def __init__(self, *args, **kwargs):
        self.name = "Visa"
        super(Visa, self).__init__(*args, **kwargs)

    def fetch_avail_currs(self):
        page = requests.get(self.url)
        tree = html.fromstring(page.content)
        options = tree.xpath(self.curr_xpath)
        codes = {o.attrib['value']: o.text[:-6].upper() for o in options
                 if len(o.attrib['value']) == 3}
        assert len(codes) != 0, 'No currencies found, check url and selector'
        return codes

    @classmethod
    def params(self, date, trans_c, card_c):
        params = dict(self.rate_params)
        params['date'] = date
        params['fromCurr'] = card_c
        params['toCurr'] = trans_c
        return urllib.parse.urlencode(params)

    @classmethod
    def rate_url(self, date, trans_c, card_c):
        return f'{self.url}?{self.params(date, trans_c, card_c)}'


class MC(Provider):

    domain = 'mastercard.co.uk'
    url = 'https://www.mastercard.co.uk/'
    curr_url = 'settlement/currencyrate/settlement-currencies'
    support_url = 'en-gb/consumers/get-support/convert-currency.html'
    rate_url = url + "settlement/currencyrate/?'{}'/conversion-rate"
    date_fmt = '%Y-%m-%d'

    rate_params = {'fxDate': None, 'transCurr': None, 'crdhldBillCurr': None,
                   'bankFee': '0.0', 'transAmt': '1'}

    def __init__(self, *args, **kwargs):

        self.referer = self.url + self.support_url
        self.curr_api = self.url + self.curr_url
        self.name = "Mastercard"
        super(MC, self).__init__(*args, **kwargs)

    def fetch_avail_currs(self):
        return dict()
        # r = requests.get(self.api, headers={"referer": self.referer})
        # codes = {x['alphaCd']: x['currNam'].strip()
        #          for x in r.json()['data']['currencies']}
        # assert len(codes) != 0, 'No currencies found, check url and selector'
        # return codes

    def params(date, trans_c, card_c):
        params = dict(self.rate_params)
        params['fxDate'] = date
        params['transCurr'] = trans_c
        params['crdhldBillCurr'] = card_c
        return urllib.parse.urlencode(params)

    def rate_url(date, trans_c, card_c):
        return self.rate_url.format(self.params(date, trans_c, card_c))


class CurrencyCode(Base):
    __tablename__ = 'currency_codes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    alpha_code = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        return f"CurrencyCode('{self.alpha_code}: {self.name})>"


class Date(Base):
    __tablename__ = 'dates'

    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False, unique=True)

    first_date = datetime.date(2016, 10, 14)
    max_days = 2000

    def date_time_to_id(self, x):
        self.first_date + datetime.timedelta(days=x)

    def __repr__(self):
        return f"<Date('{self.date}')>"


class Rate(Base):
    __tablename__ = 'rates'
    __table_args__ = (UniqueConstraint('card_id', 'trans_id',
                                       'date_id', 'provider_id'),)

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('currency_codes.id'), nullable=False)
    trans_id = Column(Integer, ForeignKey('currency_codes.id'), nullable=False)
    date_id = Column(Integer, ForeignKey('dates.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)
    rate = Column(Float)

    date = relationship('Date')
    provider = relationship('Provider')
    card_code = relationship('CurrencyCode', foreign_keys=[card_id])
    trans_code = relationship('CurrencyCode', foreign_keys=[trans_id])

    def __repr__(self):
        return f"<Rate({self.date.date} {self.provider.name}: {self.card_code.alpha_code}/{self.trans_code.alpha_code}  = {self.rate})>"
