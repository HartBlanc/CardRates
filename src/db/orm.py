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

    card_code = Column(String(3), ForeignKey('currency_codes.alpha_code'),
                       primary_key=True)

    trans_code = Column(String(3), ForeignKey('currency_codes.alpha_code'),
                        primary_key=True)

    provider_id = Column(SmallInteger, ForeignKey('providers.id'),
                         primary_key=True)

    date = Column(Date, primary_key=True)

    rate = Column(Float)

    provider = relationship('Provider')
    card_curr = relationship('CurrencyCode', foreign_keys=[card_code])
    trans_curr = relationship('CurrencyCode', foreign_keys=[trans_code])

    def __repr__(self):
        return (f"<Rate({self.date} {self.provider.name}: "
                f"{self.card_code}/{self.trans_code}  = {self.rate})>")
