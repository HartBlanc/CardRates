
    Please use the pipenv for easy setup
    installation:
        pip3 install pipenv
        pipenv install (in top directory)
    usage:
        pipenv run python db_orm.py
        pipenv shell

    Before running spider for the first time use db_orm.py to create the SQLite database.

    Spiders should be deployed using the scrapyd daemon.

    The general flow of the program is:
    (db_orm.py)
    1. check which currency codes and date ranges are available
    2. check which rates are missing from the database
    3. create a temporary input and output directory
    3. create a csv input file of these missing currencies and dates
    (scrapyd)
    1. deploy N instances of the spiders to scrapyd daemon
    (UpdaterSpider)
    1. use the csv input to build the urls and request headers
    2. request exchange rates
    3. send exchange rate info to output csv
    (post.py)
    1. merge all csv files in output directory with sqlite db
    2. delete input and output files


    Useful info:

    The approximate number of entries in the database = (Number of days) * (Number of currencies) * (Number of currencies - 1)
    Multiply this by 2 to get approx total number of requests (Visa & Mastercard)
    Mastercard goes 1 year back so to download all is approximately 365 * 153 * 152 = 8,488,440 Entries

    Nones occur when either the source (MC/Visa) does not provide that currency code, or an error occurred.
    (Two Nones means that at least one error occurred)

    To view database in sorted order execute the following statement in a DB browser:
    SELECT * FROM Rates ORDER BY card_id ASC, trans_id ASC, date_id ASC;
