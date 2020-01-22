
from datetime import date, timedelta
import sys
from pathlib import Path
from os import environ

import pytest

# Hacky solution to import errors...
sys.path[0] = str(Path(sys.path[0]) / "src")

TEST_DATE = date(day=10, month=9, year=1995)

TEST_ROWS = {
    ("GBP", "USD", TEST_DATE - timedelta(days=7), 1, 1),
    ("GBP", "USD", TEST_DATE - timedelta(days=6), 1, 2),
    ("GBP", "USD", TEST_DATE - timedelta(days=5), 1, 3),
    ("GBP", "USD", TEST_DATE - timedelta(days=4), 1, 4),
    ("GBP", "USD", TEST_DATE - timedelta(days=3), 2, 5),
    ("GBP", "USD", TEST_DATE - timedelta(days=2), 2, 6),
    ("GBP", "USD", TEST_DATE - timedelta(days=1), 2, 7),
    ("GBP", "USD", TEST_DATE, 1, 0.654654),
    ("USD", "GBP", TEST_DATE - timedelta(days=7), 1, 7),
    ("USD", "GBP", TEST_DATE - timedelta(days=6), 1, 6),
    ("USD", "GBP", TEST_DATE - timedelta(days=5), 1, 5),
    ("USD", "GBP", TEST_DATE - timedelta(days=4), 1, 4),
    ("USD", "GBP", TEST_DATE - timedelta(days=3), 2, 3),
    ("USD", "GBP", TEST_DATE - timedelta(days=2), 2, 2),
    ("USD", "GBP", TEST_DATE - timedelta(days=1), 2, 1),
}


@pytest.fixture(scope="module")
def client():

    # set up
    from db.client import DbClient
    db_url = environ.get("DB_URL")

    if "Test" not in db_url:
        name_start = db_url.rfind('/') + 1
        db_url = f"{db_url[:name_start]}Test"

    dbc = DbClient(db_url=db_url, new=True)
    # cannot have a session in the setup.

    try:
        # run tests
        yield dbc

    # tear down
    finally:
        dbc.drop_database()
        del dbc


def test_strpdate():
    from db.client import strpdate
    assert strpdate("10/09/1995") == TEST_DATE
    assert strpdate("09/10/1995", "%m/%d/%Y") == TEST_DATE


def test_current_date():
    from db.client import DbClient
    assert DbClient.current_date() is not None


def test_create_tables(client):
    tables = client.engine.table_names()
    assert set(tables) == {"providers", "currency_codes", "rates"}
    assert len(client.spiders) != 0

    from db.orm import Provider, CurrencyCode
    with client.session_scope(commit=False) as s:
        assert set(s.query(Provider.name)) == {(spider.provider,) for spider in client.spiders}
        s.close()

    avail_currencies = set()
    for spider in client.spiders:
        avail_currencies = avail_currencies.union(spider.fetch_avail_currs().keys())

    assert set(s.query(CurrencyCode.alpha_code)) == {(a,) for a in avail_currencies}


def test_missing(client):

    with client.session_scope() as s:
        from db.orm import Rate

        for card_c, trans_c, d, provider_id, rate in TEST_ROWS:
            s.add(Rate(card_code=card_c,
                       trans_code=trans_c,
                       date=d,
                       provider_id=provider_id,
                       rate=rate))
        s.commit()
        s.close()

    missing = set(client.missing("Mastercard", end=TEST_DATE, num_days=8, currs={"GBP", "USD"}))

    assert missing == {("GBP", "USD", TEST_DATE - timedelta(days=3)),
                       ("GBP", "USD", TEST_DATE - timedelta(days=2)),
                       ("GBP", "USD", TEST_DATE - timedelta(days=1)),
                       ("USD", "GBP", TEST_DATE),
                       ("USD", "GBP", TEST_DATE - timedelta(days=3)),
                       ("USD", "GBP", TEST_DATE - timedelta(days=2)),
                       ("USD", "GBP", TEST_DATE - timedelta(days=1)),
                       }
