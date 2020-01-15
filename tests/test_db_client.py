
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
    # set up
    from src.db_client import DbClient
    db_url = environ.get("DB_URL")
    name_start = db_url.rfind('/') + 1
    db_url = f"{db_url[:name_start]}Test"

    client = DbClient(db_url=db_url, new=True)

    # run test
    yield client

    # tear down
    with client.session_scope() as s:
        client.drop_database()
    del client


def test_strpdate():
    from src.db_client import strpdate
    assert strpdate("10/09/1995") == TEST_DATE
    assert strpdate("09/10/1995", "%m/%d/%Y") == TEST_DATE


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
