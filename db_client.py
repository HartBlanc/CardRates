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



        self.engine = create_engine(settings().get("CONNECTION_STRING"), echo=echo)
        self.Session = sessionmaker(bind=self.engine)

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




        with self.session_scope() as s:

                with file.open() as f:
                    data = csv.reader(f)
                    next(data)

                                   provider_id=provider_id,


    def update_currencies(self, provider):
        with self.session_scope() as s:
            for alpha_code, name in provider.avail_currs.items():
                try:
                    s.add(CurrencyCode(name=name, alpha_code=alpha_code))
                    s.commit()
                except IntegrityError:
                    s.rollback()


    def adjust_date_range(self):
        pass

    def indetify_outliers(self):
        pass


if __name__ == '__main__':
    dbc = DbClient()
    dbc.drop_all_tables()
    dbc.create_tables(Base)
    dbc.combos_to_csv(4, dbc.missing('Mastercard'), 'MasterIn')


