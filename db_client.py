from scrapy.utils.project import get_project_settings

from db_orm import CurrencyCode, Rate, Provider, Base

from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine

from contextlib import contextmanager
from itertools import product

from pytz import timezone
import datetime

from pathlib import Path
import csv

std_date_fmt = get_project_settings('STD_DATE_FMT')


class DbClient:

    def __init__(self):

        self.engine = create_engine(get_project_settings().get("CONNECTION_STRING"))
        self.Session = sessionmaker(bind=self.engine)

    @staticmethod
    def current_day():
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

    def create_tables(self, base, providers):        
        base.metadata.create_all(self.engine)

        with self.session_scope() as s:
            for p in providers:
                s.add(p)
                for alpha_code, name in p.avail_currs.items():
                    try:
                        s.add(CurrencyCode(name=name, alpha_code=alpha_code))
                        s.commit()
                    except IntegrityError:
                        s.rollback()

    def find_missing(self, provider):
        with self.session_scope(False) as s:

            avail_currs = set(provider.avail_currs.keys())

            end = self.current_date()
            start = end - datetime.timedelta(days=363)

            avail_dates = (end - datetime.timedelta(days=x) for x in range(363))

            all_combos = ((x, y, z) for x, y, z 
                          in product(avail_currs, avail_currs, avail_dates) 
                          if x != y)

            CardAlias = aliased(CurrencyCode)
            not_missing = set(s.query(CardAlias.alpha_code, CurrencyCode.alpha_code, Rate.date)
                               .join(CardAlias, Rate.card_id == CardAlias.id)
                               .join(CurrencyCode, Rate.trans_id == CurrencyCode.id)
                               .filter(Rate.provider.has(name=provider.name)))

        return (x for x in all_combos if x not in not_missing)

    # multiprocessing to be implemented
    def combos_to_csv(self, file_count, results, provider, inpath):

        paths = tuple(Path(inpath) / f'{i}.csv' for i in range(file_count))
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

    def alphaCd_to_id(self):
        with self.session_scope(False) as s:
            q = s.query(CurrencyCode.alpha_code, CurrencyCode.id)
        return {ac: id for ac, id in q}

    def rates_from_csv(self, provider_id, outpath):
        cd_to_id = self.alphaCd_to_id()

        with self.session_scope() as s:

            for file in Path(outpath).glob('*.csv'):
                print(file)
                with file.open() as f:
                    data = csv.reader(f)
                    next(data)
                    s.add_all(Rate(card_id=cd_to_id[card_code],
                                   trans_id=cd_to_id[trans_code],
                                   date=self.strpdate(date),
                                   provider_id=provider_id,
                                   rate=rate)
                              for card_code, trans_code, date, rate in data)

    def insert_new_currency(self):
        pass

    def adjust_date_range(self):
        pass

    def indetify_outliers(self):
        pass


if __name__ == '__main__':
    dbc = DbClient()
    dbc.create_tables(Base, Provider(name='Visa'), Provider(name='Mastercard'))