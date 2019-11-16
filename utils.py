from datetime import date

VISA_URL = 'https://www.visa.co.uk/support/consumer/travel-support/exchange-rate-calculator.html'
MC_URL = 'https://www.mastercard.co.uk/'
MC_SETTLEMENT = 'settlement/currencyrate/settlement-currencies'
MC_SUPPORT = 'en-gb/consumers/get-support/convert-currency.html'
FIRST_DATE = date(2016, 10, 14)



TODAY = current_day()

def current_day():
    # finds the latest day based on the mastercard definition
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    
    today = now.date()
    
    if now.hour < 14:
        today -= datetime.timedelta(days=1)

    return day_calculator(today)