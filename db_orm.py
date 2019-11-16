import sqlalchemy
from sqlalchemy import create_engine, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Float, UniqueConstraint,
                        ForeignKey)
from sqlalchemy.orm import sessionmaker, relationship, aliased

from itertools import product
from pathlib import Path
from lxml import html
import requests
import datetime
import pytz

Base = declarative_base()


def current_day():
    # finds the latest day based on the mastercard definition
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))

    today = now.date()

    if now.hour < 14:
        today -= datetime.timedelta(days=1)

    return today


def create_all_combos(cur, l1, l2):
    # all combinations where the currencies aren't the same
    return {(x, y, z) for (x, y, (z,)) in product(l1, l1, l2) if x != y}


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


class MC(Provider):

    MC_URL = 'https://www.mastercard.co.uk/'
    MC_SETTLEMENT = 'settlement/currencyrate/settlement-currencies'
    MC_SUPPORT = 'en-gb/consumers/get-support/convert-currency.html'
    date_fmt = '%Y-%m-%d'
    # self.name = "Mastercard"

    def __init__(self, *args, **kwargs):

        self.referer = self.MC_URL + self.MC_SUPPORT
        self.api = self.MC_URL + self.MC_SETTLEMENT
        self.name = "Mastercard"
        super(MC, self).__init__(*args, **kwargs)

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


def set_up(base, db_name):
    engine = create_engine(f'sqlite:///{db_name}.db')
    base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    for p in [Visa(), MC()]:
        session.add(p)
        session.add_all((CurrencyCode(name=name, alpha_code=alpha_code)
                         for alpha_code, name in p.avail_currs.items()))

    session.add_all((Date(date=Date.first_date + datetime.timedelta(days=x))
                     for x in range(0, Date.max_days)))

    session.commit()


# finds codes that are online but not in the database
# creates combos of all date/curr_pairs
# finds combos that are not in the database that should be

def fake_data(base, db_name):
    engine = create_engine(f'sqlite:///{db_name}.db')
    base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    usd_id = (session.query(CurrencyCode.id)
                     .filter(CurrencyCode.alpha_code == 'USD')
                     .first())

    gbp_id = (session.query(CurrencyCode.id)
                     .filter(CurrencyCode.alpha_code == 'GBP')
                     .first())

    my_rate = Rate(card_id=usd_id[0], trans_id=gbp_id[0],
                   date_id=976, provider_id=1, rate=1.5)
    session.add(my_rate)
    session.commit()


def find_missing(base, db_name, provider):
    engine = create_engine(f'sqlite:///{db_name}.db')
    base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    avail_currs = set(provider.avail_currs.keys())

    end = (current_day() - Date.first_date).days
    start = end - 363
    avail_dates = (session.query(Date.id)
                          .filter(Date.id > start, Date.id <= end))

    all_combos = create_all_combos(avail_currs, avail_currs, avail_dates)

    CardAlias = aliased(CurrencyCode)
    not_missing = set(session.query(CardAlias.alpha_code, CurrencyCode.alpha_code, Rate.date_id)
                             .join(CardAlias, Rate.card_id == CardAlias.id)
                             .join(CurrencyCode, Rate.trans_id == CurrencyCode.id)
                             .filter(Rate.provider.has(name=provider.name)))

    return list(all_combos-not_missing)


# multiprocessing to be implemented
def results_to_csv(file_count, results, provider):

    results = (results[i::file_count] for i in range(file_count))

    in_path = Path('./input')
    out_path = Path('./output')

    in_path.mkdir()
    out_path.mkdir()

    for i, partial_results in enumerate(results):
        print(f'writing {i+1}th file to disk')
        (in_path / f'{i}.csv').touch()
        with (in_path / f'{i}.csv').open(mode='w') as f:
            for card_c, trans_c, date_id in partial_results:
                date = Date.first_date + datetime.timedelta(date_id - 1)
                date_string = provider.date_string(provider, date)
                f.write(f'{card_c},{trans_c},{date_string}\n')
