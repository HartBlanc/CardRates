# https://docs.sqlalchemy.org/en/13/orm/tutorial.html

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Float, UniqueConstraint,
                        ForeignKey)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship


sqlalchemy.__version__


engine = create_engine('sqlite:///myting2.db')

Base = declarative_base()


class Provider(Base):
    __tablename__ = 'providers'

    # assumed that sqlalchemy won't allow null for pk
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Provider(name='{self.name}')>"


class CurrencyCode(Base):
    __tablename__ = 'currency_codes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    alpha_code = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        return f("CurrencyCode(name='{self.name}',"
                 "alpha_code='{self.alpha_code})>")


class Date(Base):
    __tablename__ = 'dates'

    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Date(name='{self.date}')>"


class Rate(Base):
    __tablename__ = 'rates'
    __table_args__ = (UniqueConstraint('card_id', 'trans_id',
                                       'date_id', 'provider_id'),)

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('currency_codes.id'), nullable=False)
    trans_id = Column(Integer, ForeignKey('currency_codes.id'), nullable=False)
    date_id = Column(Integer, ForeignKey('dates.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=False)
    rate = Column(Float)

    card_codes = relationship('CurrencyCode', foreign_keys=[card_id], backref='card_codes')
    trans_codes = relationship('CurrencyCode', foreign_keys=[trans_id], backref='trans_codes')
    dates = relationship('Date')
    providers = relationship('Provider')

    def __repr__(self):
        return f"<Rate({self.dates.date} {self.providers.name}: {self.card_codes.alpha_code}/{self.trans_codes.alpha_code}  = {self.rate})>"


Base.metadata.create_all(engine)

visa = Provider(name='Visa')
visa.name

usd = CurrencyCode(name='United States Dollar', alpha_code='USD')
gbp = CurrencyCode(name='Great British Pound', alpha_code='GBP')

first = Date(date='10-14-2016')

my_rate = Rate(card_id=1, trans_id=2, date_id=1, provider_id=1, rate=1.5)


Session = sessionmaker(bind=engine)
session = Session()
session.add_all([visa, usd, gbp, first, my_rate])  # not yet added to database, will add automatically once neccessary #
session.commit()

for instance in session.query(Rate):
    print(instance)
