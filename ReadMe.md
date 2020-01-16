[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

# CardRates
CardRates is a tool for extracting daily fiat currency exchange rates from public websites. Currently the tool can be used to retrieve rates from two international payment schemes - Visa and Mastercard with scope for other providers in the future.

## Motivation
Exchange rates are publicly available on providers websites and can be retrieved easily for a single currency pair on a single date (e.g. GBP/USD for 1st of Jan 2019). This is useful for determining the rate you were charged for a transaction. However, it is not easy to retrieve data across dates and across many currency pairs. This kind of information is necessary for consumers to make informed choices about which payment scheme to choose to get the best rates for their specific requirements.

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



## Getting Started

### Database Config 📝
First choose a SQL variant to store the rates in (any SQLAlchemy compatible DB will do).
Then create a .env file at the root of CardRates with your [Database URL](https://docs.sqlalchemy.org/en/13/core/engines.html).

```shell
$ echo DB_URL=dialect[+driver]://user:password@host/dbname > .env
```

Note: You may need to install a DB API library to connect to your database. Check the SQLAlchemy docs for supported APIs.

### Installing Packages 🐍
In the root directory run:
```shell
$ pipenv sync  # include --dev flag for development packages
$ pipenv shell
```

### Create Tables and Generate csv 📝
In the src directory run:
```shell
$ python createCSV.py --new # (new flag is for creating a new database)
```

## Code Example
### Run Spiders 🕷
In the src directory run:
```shell 
$ scrapy crawl MCSpider -a in_path=MastercardInput/0.csv
```
```shell
$ scrapy crawl VisaSpider -a in_path=VisaInput/0.csv
```

## Contact
[callumjameshart@gmail.com](mailto:callumjameshart@gmail.com)
