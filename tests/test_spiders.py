from datetime import date
import sys
from csv import reader
from pathlib import Path

# Hacky solution to import errors...
sys.path[0] = str(Path(sys.path[0]) / "src")

TEST_DATE = date(day=10, month=9, year=2019)


def test_visa_spider():
    from cardRatesUpdater.spiders.VisaSpider import VisaSpider
    from scrapy.crawler import CrawlerProcess

    in_path = Path("tests/visa_test_input.csv")
    out_path = Path("tests/out.csv")

    test_input = '''GBP,USD,03/09/2019
GBP,USD,04/09/2019
GBP,USD,05/09/2019
GBP,USD,06/09/2019
GBP,USD,07/09/2019
GBP,USD,08/09/2019
GBP,USD,09/09/2019
GBP,USD,10/09/2019
USD,GBP,03/09/2019
USD,GBP,04/09/2019
USD,GBP,05/09/2019
USD,GBP,06/09/2019
USD,GBP,07/09/2019
USD,GBP,08/09/2019
USD,GBP,09/09/2019
USD,GBP,10/09/2019
'''

    test_output = [
                    {"GBP", "USD", "03/09/2019", "0.830965"},
                    {"GBP", "USD", "04/09/2019", "0.836247"},
                    {"GBP", "USD", "05/09/2019", "0.830482"},
                    {"GBP", "USD", "06/09/2019", "0.819053"},
                    {"GBP", "USD", "07/09/2019", "0.815047"},
                    {"GBP", "USD", "08/09/2019", "0.815047"},
                    {"GBP", "USD", "09/09/2019", "0.815047"},
                    {"GBP", "USD", "10/09/2019", "0.817513"},
                    {"USD", "GBP", "03/09/2019", "1.218278"},
                    {"USD", "GBP", "04/09/2019", "1.210679"},
                    {"USD", "GBP", "05/09/2019", "1.225977"},
                    {"USD", "GBP", "06/09/2019", "1.235476"},
                    {"USD", "GBP", "07/09/2019", "1.234977"},
                    {"USD", "GBP", "08/09/2019", "1.234977"},
                    {"USD", "GBP", "09/09/2019", "1.234977"},
                    {"USD", "GBP", "10/09/2019", "1.238676"},
                  ]

    with in_path.open("w") as f:
        f.write(test_input)

    # todo can you get_project_settings?
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'csv',
        'FEED_URI': str(out_path.resolve()),
        'EXPORT_FIELDS': ['card_c', 'trans_c', 'date', 'rate']
    })

    process.crawl(VisaSpider, in_path=str(in_path))
    process.start()

    with out_path.open() as f:
        results = reader(f)
        next(results)
        results = [set(r) for r in results]

    assert len(results) == len(test_output)
    for result in results:
        assert result in test_output
