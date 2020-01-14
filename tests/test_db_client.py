
from datetime import date
import sys
from pathlib import Path

# Hacky solution to import errors...
sys.path[0] = str(Path(sys.path[0]) / "src")

TEST_DATE = date(day=10, month=9, year=1995)


def test_strpdate():
    from src.db_client import strpdate
    assert strpdate("10/09/1995") == TEST_DATE
    assert strpdate("10/10/1995", "%m/%d/%Y") == TEST_DATE


def test_current_date():
    from src.db_client import DbClient
    assert DbClient.current_date() is not None

# set up new database
# check that there are three tables, with the right names, check that they are not empty
# delete the database
# def test_create_tables():
#     from src.db_client import DbClient
#     from src.db_orm import Base
#     client = DbClient()
#     client.create_tables(Base, conn_string=...)
