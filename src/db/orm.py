# -*- coding: utf-8 -*-
from sqlalchemy import (Column, Integer, SmallInteger, String,
                        Float, Date, UniqueConstraint, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Provider(Base):
    __tablename__ = 'providers'

    # assumed that SQLAlchemy won't allow null for pk
    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Provider(name='{self.name}')>"


class CurrencyCode(Base):
    __tablename__ = 'currency_codes'

    alpha_code = Column(String(3), primary_key=True)
    name = Column(String(50), nullable=False)

    def __repr__(self):
        return f"CurrencyCode('{self.alpha_code}: {self.name})>"


class Rate(Base):
    __tablename__ = 'rates'
    __table_args__ = (UniqueConstraint('card_code', 'trans_code',
                                       'date', 'provider_id'),)

    id = Column(Integer, primary_key=True)

    card_code = Column(String(3), ForeignKey('currency_codes.alpha_code'),
                       nullable=False)

    trans_code = Column(String(3), ForeignKey('currency_codes.alpha_code'),
                        nullable=False)

    provider_id = Column(SmallInteger, ForeignKey('providers.id'),
                         nullable=False)

    date = Column(Date, nullable=False)
    rate = Column(Float)

    provider = relationship('Provider')
    card_curr = relationship('CurrencyCode', foreign_keys=[card_code])
    trans_curr = relationship('CurrencyCode', foreign_keys=[trans_code])

    def __repr__(self):
        return (f"<Rate({self.date} {self.provider.name}: "
                f"{self.card_code}/{self.trans_code}  = {self.rate})>")
