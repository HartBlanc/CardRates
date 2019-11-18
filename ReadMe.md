
    Please use the pipenv for easy setup
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
