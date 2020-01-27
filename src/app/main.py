from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from wtforms import DateField
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://rsmarincu:temp@cardrates.c0nomd60mbxj.eu-west-2.rds.amazonaws.com:3306/CardRates?charset=utf8'
app.secret_key="test"
db = SQLAlchemy(app)


class Dateform(Form):
    dt = DateField("", format="%d%m%Y")



# @app.route('/', methods=['GET', 'POST'])
# def hello():
#     return render_template("cardrates.html")

@app.route('/', methods=['GET', 'POST'])
def getDate():
    form = Dateform()
    if form.validate_on_submit():
        return form.dt.data.strftime('%x')
    return render_template("cardrates.html", form=form)



class CurrencyCode(db.Model):
    __tablename__ = 'currency_codes'

    alpha_code = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"CurrencyCode('{self.alpha_code}: {self.name})>"
