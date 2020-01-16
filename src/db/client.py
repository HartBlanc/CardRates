# -*- coding: utf-8 -*-

from os import environ
from scrapy import spiderloader
from scrapy.utils.project import get_project_settings as settings

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import MetaData
from sqlalchemy import create_engine

from sqlalchemy_utils.functions import create_database, drop_database

from contextlib import contextmanager
from itertools import product

from pytz import timezone
import datetime

from pathlib import Path
import csv


from .orm import CurrencyCode, Rate, Provider, Base

std_date_fmt = settings().get('STD_DATE_FMT')


def strpdate(date, fmt=std_date_fmt):
    return datetime.datetime.strptime(date, fmt).date()


class DbClient:

    def __init__(self, db_url=environ.get("DB_URL"), new=False,
                 echo=False):

        self.engine = create_engine(db_url, echo=echo)
        self.session_maker = sessionmaker(bind=self.engine)
        self.metadata = MetaData(bind=self.engine)

        spider_loader = spiderloader.SpiderLoader.from_settings(settings())
        s_names = spider_loader.list()
        self.spiders = tuple(spider_loader.load(name) for name in s_names)

        # todo consider wrapping sqlalchemy.exc.OperationalError instead of using new parameter
        if new:
            create_database(self.engine.url)
            self.create_tables(Base)
        else:
            self.metadata.reflect()

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

        session = self.session_maker()
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
            providers = [s.provider for s in self.spiders]
            for pid, p_name in enumerate(providers):
                s.add(Provider(id=pid + 1, name=p_name))
                self.update_currencies(p_name)

    # todo differentiate between card currencies and transaction currencies
    def missing(self, provider, end=None, num_days=363, currs=None):
        with self.session_scope(commit=False) as s:

            if not end:
                end = self.current_date()

            start = end - datetime.timedelta(days=num_days - 1)

            spider = next(spider for spider in self.spiders
                          if spider.provider == provider)

            if not currs:
                currs = set(spider.fetch_avail_currs().keys())

            avail_dates = (end - datetime.timedelta(days=x)
                           for x in range(num_days))

            all_combos = ((x, y, z) for x, y, z
                          in product(currs, currs, avail_dates)
                          if x != y)

            not_missing = set(s.query(Rate.card_code, Rate.trans_code,
                                      Rate.date)
                               .filter(Rate.provider.has(name=provider))
                               .filter(Rate.date <= end)
                               .filter(Rate.date >= start)
                               .filter(Rate.card_code.in_(currs))
                               .filter(Rate.trans_code.in_(currs))
                              )

        return (x for x in all_combos if x not in not_missing)

    # todo multiprocessing to be implemented
    @staticmethod
    def combos_to_csv(file_count, results, out_path):

        out_path = Path(out_path)

        try:
            out_path.mkdir()
        except FileExistsError:
            pass

        paths = tuple(out_path / f'{i}.csv' for i in range(file_count))

        for p in paths:
            p.touch()

        try:
            fs = tuple(p.open(mode='w') for p in paths)
            for i, (card_c, trans_c, date) in enumerate(results):
                std_date = date.strftime(std_date_fmt)
                fs[i % file_count].write(f'{card_c},{trans_c},{std_date}\n')

        finally:
            for f in fs:
                f.close()

    def rates_from_csv(self, provider, in_path):

        with self.session_scope() as s:

            provider_id = (s.query(Provider.id).filter_by(name=provider)
                            .first()[0])

            for file in Path(in_path).glob('*.csv'):
                print(file)
                with file.open() as f:
                    data = csv.reader(f)
                    next(data)  # skip header row #
                    rates = [Rate(card_code=card_code,
                                  trans_code=trans_code,
                                  date=strpdate(date, fmt='%m/%d/%Y'),
                                  provider_id=provider_id,
                                  rate=rate)
                             for card_code, trans_code, date, rate in data]
                    s.bulk_save_objects(rates)
                    s.commit()

    def update_currencies(self, provider):
        spider = next(s for s in self.spiders if s.provider == provider)
        with self.session_scope() as s:
            for alpha_code, name in spider.fetch_avail_currs().items():
                try:
                    s.add(CurrencyCode(alpha_code=alpha_code, name=name))
                    s.commit()
                except IntegrityError:
                    s.rollback()

    def drop_all_tables(self):
        self.metadata.drop_all()

    def drop_database(self):
        drop_database(self.engine.url)