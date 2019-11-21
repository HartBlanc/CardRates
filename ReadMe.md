## CardRates
CardRates is a tool for extracting daily fiat currency exchange rates from public websites. Currently the tool can be used to retrieve rates from the two international payment schemes - Visa and Mastercard with scope for other providers in the future.

## Motivation
These exchange rates are publicly available on providers websites and can be retrieved easily for a single currency pair on a single date (e.g. GBP/USD for 1st of Jan 2019), which is useful for determining the rate you were charged for a transaction. However, it is not easy to retrieve data across dates and across many currency pairs. This kind of information is neccessary for consumers to make informed choices about which payment scheme to choose to get the best rates for their specific requirements.

## Build status
Tests are currently in development.

[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
 
## Screenshots
Include logo/demo screenshot etc.

## Tech/framework used
<b>Built with</b>
- [Scrapy](https://github.com/scrapy/scrapy)
- [Python](https://www.python.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

## Features
- Retrieve exchange rates for all available dates and currency pairs
- Retrieve the currently offered settlement currencies from each provider

## Code Example
Show what the library does as concisely as possible, developers should be able to figure out **how** your project solves their problem by looking at the code example. Make sure the API you are showing off is obvious, and that your code is short and concise.

## Installation
Provide step by step series of examples and explanations about how to get a development env running.

## API Reference

Depending on the size of the project, if it is small and simple enough the reference docs can be added to the README. For medium size to larger projects it is important to at least provide a link to where the API reference docs live.

## Tests
Describe and show how to run the tests with code examples.

## How to use?
If people like your project they’ll want to learn how they can use it. To do so include step by step guide to use your project.

## Contribute

Let people know how they can contribute into your project. A [contributing guideline](https://github.com/zulip/zulip-electron/blob/master/CONTRIBUTING.md) will be a big plus.

## Credits
Give proper credits. This could be a link to any repo which inspired you to build this project, any blogposts or links to people who contrbuted in this project. 

#### Anything else that seems useful

## License
A short snippet describing the license (MIT, Apache etc)

MIT © [Yourname]()




    Please use pipenv for easy setup
    installation:
        pip3 install pipenv
        pipenv install (in top directory)
    usage:
        pipenv run python db_orm.py
        pipenv shell

    Before running spider for the first time:
    1. Update the settings.py to configure your db connection
    2. use db_client.py to initialise the database.

    The general flow of the program is:
    (db_client.py)
    1. check which currency codes and date ranges are available
    2. check which rates are missing from the database
    3. create a temporary input and output directory
    3. create a csv input file of these missing currencies and dates
    4. deploy spiders (e.g. using "pipenv run scrapy crawl MCSpider -a inpath=input/0.csv"
    (UpdaterSpider)
    1. uses the csv input to build the urls and request headers
    2. request exchange rates
    3. send exchange rate info to db
    (db_client.py)
    1. load rates from csv


    Useful info:

    The approximate number of entries in the database = (Number of days) * (Number of currencies) * (Number of currencies - 1)
    Multiply this by 2 to get approx total number of requests (Visa & Mastercard)
    Mastercard goes 1 year back so to download all is approximately 365 * 162 * 161 = 9,519,930 Entries
