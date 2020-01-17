from sys import argv
from db.client import DbClient

if __name__ == "__main__":

    if len(argv) > 1 and argv[1].lower().strip() == "--new":
        dbc = DbClient(new=True)
    else:
        dbc = DbClient()

    for spider in dbc.spiders:
        p = spider.provider
        dbc.combos_to_csv(1, dbc.missing(p), f'{p}Input')
