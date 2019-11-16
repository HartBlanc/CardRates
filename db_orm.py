import sqlalchemy
from inspect import getmembers
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Float, UniqueConstraint,
                        ForeignKey)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
import requests
from lxml import html
import datetime


engine = create_engine('sqlite:///myting2.db')

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

    VISA_URL = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
    VISA_XPATH = '//*[@id="fromCurr"]/option'
    date_fmt = '%m/%d/%Y'

    def __init__(self, *args, **kwargs):
        self.xpath = self.VISA_XPATH
        self.url = self.VISA_URL
        super(Visa, self).__init__(*args, **kwargs)
        self.name = 'Visa'
        print(self.avail_currs)

    def fetch_avail_currs(self):
        page = requests.get(self.url)
        tree = html.fromstring(page.content)
        options = tree.xpath(self.xpath)
        codes = {o.attrib['value']: o.text[:-6].upper() for o in options
                 if len(o.attrib['value']) == 3}
        assert len(codes) != 0, 'No currencies found, check url and selector'
        return codes


class MC(Provider):

    MC_URL = 'https://www.mastercard.co.uk/'
    MC_SETTLEMENT = 'settlement/currencyrate/settlement-currencies'
    MC_SUPPORT = 'en-gb/consumers/get-support/convert-currency.html'
    date_fmt = '%Y-%m-%d'

    def __init__(self, *args, **kwargs):

        self.referer = self.MC_URL + self.MC_SUPPORT
        self.api = self.MC_URL + self.MC_SETTLEMENT
        super(MC, self).__init__(*args, **kwargs)
        self.name = "Mastercard"
        print(self.avail_currs)

    def fetch_avail_currs(self):
        return dict()
        # r = requests.get(self.api, headers={"referer": self.referer})
        # codes = {x['alphaCd']: x['currNam'].strip()
        #          for x in r.json()['data']['currencies']}
        # assert len(codes) != 0, 'No currencies found, check url and selector'
        # return codes


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

    card_codes = relationship('CurrencyCode', foreign_keys=[card_id], backref='card_codes')
    trans_codes = relationship('CurrencyCode', foreign_keys=[trans_id], backref='trans_codes')
    dates = relationship('Date')
    providers = relationship('Provider')

    def __repr__(self):
        return f"<Rate({self.dates.date} {self.providers.name}: {self.card_codes.alpha_code}/{self.trans_codes.alpha_code}  = {self.rate})>"


def set_up():
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()


    for p in [Visa(), MC()]:
        session.add(p)
        session.add_all((CurrencyCode(name=name, alpha_code=alpha_code) for alpha_code, name in p.avail_currs.items()))

    session.add_all((Date(date=Date.first_date + datetime.timedelta(days=x))
                     for x in range(0, Date.max_days)))

    session.commit()

