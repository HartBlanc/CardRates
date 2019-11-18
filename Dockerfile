FROM python:3

ADD CardRatesUpdater /CardRatesUpdater
ADD .scrapy.conf /
ADD scrapy.cfg /
ADD Pipfile /
ADD Pipfile.lock /
ADD 0.csv /input/0.csv
ADD db_orm.py /

RUN pip install pipenv

RUN pipenv install

CMD ["pipenv", "run", "scrapy", "crawl", "VisaSpider", "-a", "number=0", "--set", "FEED_URI=./out.csv"]