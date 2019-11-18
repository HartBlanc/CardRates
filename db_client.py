# -*- coding: utf-8 -*-
from scrapy.utils.project import get_project_settings as settings

from db_orm import CurrencyCode, Rate, Provider, Base

from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import MetaData
from sqlalchemy import create_engine

from contextlib import contextmanager
from itertools import product

from scrapy.utils import project
from scrapy import spiderloader

from pytz import timezone
import datetime

from pathlib import Path
import csv


std_date_fmt = settings().get('STD_DATE_FMT')


class DbClient:

    def __init__(self, echo=False):

        self.engine = create_engine(settings().get("CONNECTION_STRING"), echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData(bind=self.engine)
        self.metadata.reflect()
        spider_loader = spiderloader.SpiderLoader.from_settings(settings())
        s_names = spider_loader.list()
        self.spiders =tuple(spider_loader.load(name) for name in s_names)

    @staticmethod
    def current_date():
        # finds the latest day based on the mastercard definition
        now = datetime.datetime.now(timezone('US/Eastern'))

        today = now.date()

        if now.hour < 14:
            today -= datetime.timedelta(days=1)

        return today

    @contextmanager
    def session_scope(self, commit=True):
        """Provide a transactional scope around a series of operations."""

        session = self.Session()
        try:
            yield session
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self, base):
        base.metadata.create_all(self.engine)

        with self.session_scope() as s:
            for spider in self.spiders:
                s.add(Provider(name=spider.provider))
                for alpha_code, name in spider.fetch_avail_currs().items():
                    print(alpha_code, name)
                    s.merge(CurrencyCode(alpha_code=alpha_code, name=name))

    def missing(self, provider):
        with self.session_scope(False) as s:

            spider = next(spider for spider in self.spiders 
                          if spider.provider == provider)

            avail_currs = set(spider.fetch_avail_currs().keys())

            end = self.current_date()
            start = end - datetime.timedelta(days=363)

            avail_dates = (end - datetime.timedelta(days=x)
                           for x in range(363))

            all_combos = ((x, y, z) for x, y, z
                          in product(avail_currs, avail_currs, avail_dates)
                          if x != y)

            not_missing = set(s.query(Rate.card_code, Rate.trans_code, Rate.date)
                               .filter(Rate.provider.has(name=provider)))

        return (x for x in all_combos if x not in not_missing)

    # multiprocessing to be implemented
    def combos_to_csv(self, file_count, results, outpath):

        outpath = Path(outpath)
        outpath.mkdir()
        paths = tuple(outpath / f'{i}.csv' for i in range(file_count))
        for p in paths:
            p.touch()

        try:
            files = tuple(p.open(mode='w') for p in paths)
            for i, (card_c, trans_c, date) in enumerate(results):
                date_string = date.strftime(std_date_fmt)
                files[i % (file_count)].write(f'{card_c},{trans_c},{date_string}\n')

        finally:
            for f in files:
                f.close()

    def strpdate(self, date):
        return datetime.datetime.strptime(date, std_date_fmt).date()

    def rates_from_csv(self, provider_id, inpath):

        with self.session_scope() as s:

            for file in Path(inpath).glob('*.csv'):
                print(file)
                with file.open() as f:
                    data = csv.reader(f)
                    next(data)
                    s.add_all(Rate(card_code=card_code,
                                   trans_code=trans_code,
                                   date=self.strpdate(date),
                                   provider_id=provider_id,
                                   rate=rate)
                              for card_code, trans_code, date, rate in data)
    
    def drop_all_tables(self):
        self.metadata.drop_all()

    def insert_new_currency(self):
        pass

    def adjust_date_range(self):
        pass

    def indetify_outliers(self):
        pass


if __name__ == '__main__':
    dbc = DbClient()
    dbc.drop_all_tables()
    dbc.create_tables(Base)
    dbc.combos_to_csv(4, dbc.missing('Mastercard'), 'MasterIn')

