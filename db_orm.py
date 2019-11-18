# -*- coding: utf-8 -*-
from sqlalchemy import (Column, Integer, SmallInteger, String,
                        Float, Date, UniqueConstraint, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Provider(Base):
    __tablename__ = 'providers'

    # assumed that sqlalchemy won't allow null for pk
    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Provider(name='{self.name}')>"


class CurrencyCode(Base):
    __tablename__ = 'currency_codes'

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False)
    alpha_code = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        return f"CurrencyCode('{self.alpha_code}: {self.name})>"


class Rate(Base):
    __tablename__ = 'rates'
    __table_args__ = (UniqueConstraint('card_id', 'trans_id',
                                       'date', 'provider_id'),)

    id = Column(Integer, primary_key=True)

    card_id = Column(SmallInteger, ForeignKey('currency_codes.id'),
                     nullable=False)

    trans_id = Column(SmallInteger, ForeignKey('currency_codes.id'),
                      nullable=False)

    provider_id = Column(SmallInteger, ForeignKey('providers.id'),
                         nullable=False)

    date = Column(Date, nullable=False)
    rate = Column(Float)

    provider = relationship('Provider')
    card_code = relationship('CurrencyCode', foreign_keys=[card_id])
    trans_code = relationship('CurrencyCode', foreign_keys=[trans_id])

    def __repr__(self):
        return f"<Rate({self.date} {self.provider.name}: {self.card_code.alpha_code}/{self.trans_code.alpha_code}  = {self.rate})>"
