from flask import Flask, render_template, jsonify, request
from json import load

with open("static/currency_country_map.json") as f:
    currency_country_map = load(f)

app = Flask(__name__)


@app.route('/home/')
def render_static():
    return render_template('home.html')


# should percentile rank be based on currency pairs, not countries?
# causes lumpiness in currency blocks.
@app.route('/rates')
def rates_by_country():
    from db.client import DbClient
    dbc = DbClient()

    response = {}

    response['relative_rates'] = []

    currency_rate_map = dbc.average_rate_by_currency(request.args.get("card_curr"))

    for id, currency_code in currency_country_map.items():
        try:
            mc, visa = currency_rate_map[currency_code]
            relative_rate = (1 - visa / mc) if (visa <= mc) else -(1 - mc / visa)
            response['relative_rates'].append({"id": id, "rate": relative_rate})
        except KeyError:
            print("Missing Currency Code:", currency_code)

    abs_rates = sorted([abs(row["rate"]) for row in response['relative_rates']])
    n = len(abs_rates)

    response['quartiles'] = abs_rates[0], abs_rates[n // 4], abs_rates[n // 2], abs_rates[n * 3 // 4], abs_rates[n - 4]

    for row in response['relative_rates']:
        if row["rate"] > 0:
            row["rate"] = sum(rate < row["rate"] for rate in abs_rates) / n
        elif row["rate"] < 0:
            row["rate"] = -sum(rate < abs(row["rate"]) for rate in abs_rates) / n
        else:
            row["rate"] = 0

    return jsonify(response)


if __name__ == '__main__':
    app.run()
