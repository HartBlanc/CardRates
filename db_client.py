from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.exc import IntegrityError
from itertools import product
from pathlib import Path
from contextlib import contextmanager
import pytz
import csv
from db_orm import *


class DbClient:

    def __init__(self, db_name, conn_string=None):
        
        if conn_string is None:
            conn_string = f'sqlite:///{db_name}.db'

        self.engine = create_engine(conn_string)
        self.Session = sessionmaker(bind=self.engine)

    @staticmethod
    def current_day():
        # finds the latest day based on the mastercard definition
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))

        today = now.date()

        if now.hour < 14:
            today -= datetime.timedelta(days=1)

        return today

    @staticmethod
    def create_all_combos(cur, l1, l2):
        # all combinations where the currencies aren't the same
        return ((x, y, z) for (x, y, z) in product(l1, l1, l2) if x != y)

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

            for p in providers:
                update_currencies(provider)

            s.add_all((Date(date=Date.first_date + datetime.timedelta(days=x))
                            for x in range(0, Date.max_days)))


    def fake_data(self):
        with self.session_scope() as s:

            usd_id = (self.session.query(CurrencyCode.id)
                                  .filter(CurrencyCode.alpha_code == 'USD')
                                  .first())

            gbp_id = (self.session.query(CurrencyCode.id)
                                  .filter(CurrencyCode.alpha_code == 'GBP')
                                  .first())

            my_rate = Rate(card_id=usd_id[0], trans_id=gbp_id[0],
                           date_id=976, provider_id=1, rate=1.5)
            s.add(my_rate)

    def find_missing(self, provider):
        with self.session_scope(False) as s:

            avail_currs = set(provider.avail_currs.keys())

            end = (self.current_day() - Date.first_date).days
            start = end - 363
            avail_date_ids = range(start, end + 1)

            all_combos = self.create_all_combos(avail_currs, avail_currs, avail_date_ids)

            CardAlias = aliased(CurrencyCode)
            not_missing = set(s.query(CardAlias.alpha_code, CurrencyCode.alpha_code, Rate.date_id)
                               .join(CardAlias, Rate.card_id == CardAlias.id)
                               .join(CurrencyCode, Rate.trans_id == CurrencyCode.id)
                               .filter(Rate.provider.has(name=provider.name)))

        return (x for x in all_combos if x not in not_missing)

    # multiprocessing to be implemented
    def results_to_csv(self, file_count, results, provider, inpath):

        paths = tuple(Path(inpath) / f'{i}.csv' for i in range(file_count))
        for p in paths:
            p.touch()

        try:
            files = tuple(p.open(mode='w') for p in paths)
            for i, (card_c, trans_c, date_id) in enumerate(results):
                date = Date.first_date + datetime.timedelta(date_id - 1)
                date_string = provider.date_string(date)
                files[i % (file_count)].write(f'{card_c},{trans_c},{date_string}\n')

        finally:
            for f in files:
                f.close()

    def alphaCd_to_id(self):
        with self.session_scope(False) as s:
            q = s.query(CurrencyCode.alpha_code, CurrencyCode.id)
        return {ac: id for ac, id in q}

    def date_to_id(self, date, fmt):
        d = datetime.datetime.strptime(date, fmt).date()
        return (d - Date.first_date).days + 1

    def import_results_from_csv(self, provider, outpath):
        cd_to_id = self.alphaCd_to_id()
        
        with self.session_scope() as s:
            provider_id = s.query(Provider.id).filter(Provider.name==provider.name).first()[0]
            print(provider_id)
            print(provider.name)
            for file in Path(outpath).glob('*.csv'):
                print(file)            
                with file.open() as f:
                    data = csv.reader(f)
                    next(data)
                    for card_code, trans_code, date, rate in data:
                        if rate == '':
                            continue
                        s.add(Rate(card_id=cd_to_id[card_code],
                                   trans_id=cd_to_id[trans_code],
                                   date_id=self.date_to_id(date, provider.date_fmt),
                                   provider_id=provider_id,
                                   rate=rate))
                file.unlink()
            Path(outpath).rmdir()
        
        

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

    input_key = ''
    
    db_name = input('what is the filename of your database?: ')
    dbc = DbClient(db_name)

    print('input q to quit')
    while input_key != 'q':
        print(''' 
              1. create tables
              2. export missing rates to csv
              3. import scraped rates to db from csv
              4. retrieve new currencies
              ''')
        input_key = input('What would you like to do?: ')
        
        if input_key == '1':
            dbc.create_tables(Base, (Visa(), MC()))
        
        elif input_key == '2':
            no_of_files = int(input('how many csv files?: '))
            provider = input('Which provider?: ').replace(' ', '').lower()
            inpath = input('csv file directory?: ')

            if provider == 'visa':
                dbc.results_to_csv(4, dbc.find_missing(Visa()), Visa(), inpath)

            elif provider in ('mc', 'mastercard'):
                dbc.results_to_csv(4, dbc.find_missing(MC()), MC(), inpath)

            else:
                print('provider not recognised: try visa or mc')

        elif input_key == '3':
            provider = input('Who is the provider?: ').replace(' ', '')
            outpath = input('csv file directory?: ')

            if provider == 'visa':
                dbc.import_results_from_csv(Visa, outpath)

            elif provider in ('mc', 'mastercard'):
                dbc.import_results_from_csv(MC, outpath)

            else:
                print('provider not recognised: try visa or mc')

        elif input_key == '4':
            provider = input('Who is the provider?: ').replace(' ', '')

            if provider == 'visa':
                dbc.update_currencies(Visa())

            elif provider in ('mc', 'mastercard'):
                dbc.update_currencies(MC())

            else:
                print('provider not recognised: try visa or mc')


        elif input_key == 'q':
            break

        else:
            print('key not recognised, input 1, 2 or 3 or q to quit')
