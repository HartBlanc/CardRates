from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

import sqlalchemy
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import MetaData

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.fields.html5 import DateField
from datetime import date
from ..db.orm import Rate, CurrencyCode, Provider

DB_URL = "mysql://rsmarincu:temp@cardrates.c0nomd60mbxj.eu-west-2.rds.amazonaws.com:3306/CardRates?charset=utf8"

app = Flask(__name__)
Bootstrap(app)
app.secret_key="test"

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData(engine)

card_query = session.query(CurrencyCode).distinct()
codes = []

for value in card_query:
    codes.append((value.alpha_code, value.name))

class Dateform(FlaskForm):
    dt = DateField("Please select a date", format="%Y-%m-%d", id='single_date')
    card_code = SelectField('From', choices=codes)
    trans_code = SelectField('To', choices=codes)
    submit_date = SubmitField('Submit')

class Compareform(FlaskForm):
    dt_from = DateField("Date from", format="%Y-%m-%d", id='date_from')
    dt_to = DateField("Date to", format="%Y-%m-%d",id='date_to')
    card_code = SelectField('From', choices=codes)
    trans_code = SelectField('To', choices=codes)
    submit_compare = SubmitField('Submit')

@app.route('/', methods=['POST', 'GET'])
def main():
    date_form = Dateform()
    compare_form = Compareform()

    if date_form.is_submitted() and date_form.submit_date.data:
        if date_form.validate():
            date = date_form.dt.data
            card_code = date_form.card_code.data
            trans_code = date_form.trans_code.data
            rate = getRate(date, card_code, trans_code, 1)
            return str(rate)

    if compare_form.is_submitted() and compare_form.submit_compare.data:
        if compare_form.validate():
            date_from = compare_form.dt_from.data
            date_to = compare_form.dt_to.data
            card_code = compare_form.card_code.data
            trans_code = compare_form.trans_code.data
            rates = compareRates(date_from, date_to, card_code, trans_code)
            return rates

    return render_template("cardrates.html", date_form=date_form, compare_form=compare_form)

def getRate(date, card_code, trans_code, provider_id):

    query = session.query(Rate).\
        filter(Rate.card_code == card_code).\
        filter(Rate.trans_code == trans_code).\
        filter(Rate.provider_id == provider_id).\
        filter(Rate.date == date)
    if query.all():
        return query[0].rate
    else:
        return "No data available"

def compareRates(date_from, date_to, card_code, trans_code):
    print("test")
    query_visa = session.query(Rate.rate).\
        filter(Rate.provider_id == 2).\
        filter(Rate.card_code == card_code).\
        filter(Rate.trans_code == trans_code).\
        filter(Rate.date > date_from).\
        filter(Rate.date < date_to).\
        order_by(Rate.date)

    query_mastercard = session.query(Rate.rate).\
        filter(Rate.provider_id == 1).\
        filter(Rate.card_code == card_code).\
        filter(Rate.trans_code == trans_code).\
        filter(Rate.date > date_from).\
        filter(Rate.date < date_to).\
        order_by(Rate.date)

    visa_rates = query_visa.all()
    mastercard_rates = query_visa.all()

    rates = {
        'visa': visa_rates,
        'mastercard': mastercard_rates
    }

    return rates

if __name__ == '__main__':
    app.run(debug=True)

