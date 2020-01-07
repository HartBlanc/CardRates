[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

# CardRates
CardRates is a tool for extracting daily fiat currency exchange rates from public websites. Currently the tool can be used to retrieve rates from two international payment schemes - Visa and Mastercard with scope for other providers in the future.

## Motivation
Exchange rates are publicly available on providers websites and can be retrieved easily for a single currency pair on a single date (e.g. GBP/USD for 1st of Jan 2019). This is useful for determining the rate you were charged for a transaction. However, it is not easy to retrieve data across dates and across many currency pairs. This kind of information is neccessary for consumers to make informed choices about which payment scheme to choose to get the best rates for their specific requirements.

## Build Status
Tests are currently in development, spiders are functioning as expected in the development environment.

## Built with
- [Scrapy](https://github.com/scrapy/scrapy)
- [Python](https://www.python.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

## Features
- Retrieve exchange rates for all available dates and currency pairs
- Retrieve the set of currently offered settlement currencies from each provider
- Limited database client api


## Code Example
```shell 
$ scrapy crawl MCSpider -a inpath=input/0.csv
```
```shell
$ scrapy crawl VisaSpider -a inpath=input/0.csv
```
## Getting Started

### Database Config
first update CardRatesUpdater/settings.py with your database details.
And create a .env at the root of CardRates file with your database password if neccessary

```shell
$ echo MYSQL_PW=YOUR_PASSWORD >.env
```

### Installing Packages
```shell
$ pipenv install  # include --dev flag for development packages
$ pipenv shell
```

### Create Tables and Generate csv
```shell
$ python db_client.py 
```
### Run Spider
```shell
$ scrapy crawl VisaSpider -a inpath=input/0.csv
```

## Contact
callumjameshart@gmail.com
