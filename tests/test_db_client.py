
from datetime import date
import sys
from pathlib import Path
from os import environ

import pytest

# Hacky solution to import errors...
sys.path[0] = str(Path(sys.path[0]) / "src")

TEST_DATE = date(day=10, month=9, year=1995)


@pytest.fixture()
def db_client():
    from src.db_client import DbClient
    from src.db_orm import Base
    conn_string = "{drivername}://{user}:{passwd}@{host}:{port}/{db_name}?charset=utf8".format(
        drivername="mysql",
        user="root",
        passwd=environ['MYSQL_PW'],
        host="localhost",
        port="3306",
        db_name="TestCardRates",
    )

    client = DbClient(conn_string=conn_string, new=True)
    yield client
    with client.session_scope() as s:
        client.drop_database()
    del client


def test_strpdate():
    from src.db_client import strpdate
    assert strpdate("10/09/1995") == TEST_DATE
    assert strpdate("10/10/1995", "%m/%d/%Y") == TEST_DATE


def test_current_date():
    from src.db_client import DbClient
    assert DbClient.current_date() is not None


def test_create_tables(db_client):
    tables = db_client.engine.table_names()
    assert set(tables) == {"providers", "currency_codes", "rates"}

    from src.db_orm import Provider, CurrencyCode
    with db_client.session_scope(commit=False) as s:
        assert set(s.query(Provider.name)) == {(spider.provider,) for spider in db_client.spiders}

        avail_currencies = set()
        for spider in db_client.spiders:
            avail_currencies = avail_currencies.union(spider.fetch_avail_currs().keys())

        assert set(s.query(CurrencyCode.alpha_code)) == {(a,) for a in avail_currencies}
