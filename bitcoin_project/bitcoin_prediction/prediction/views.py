from django.shortcuts import render
from rest_framework.views import APIView

from .populate_db import load_data
from .queueing_model_simulation import Simulation1
import requests
from datetime import date, timedelta, datetime
from flask import Markup
import pandas as pd
import plotly
import plotly.express as px
URL = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}"

# Create your views here.
def main(request):
    return render(request, 'base.html')

def population(request):
    load_data(request)
    return render(request, 'base.html')

def test(request):
    return render(request, 'test.html')

class SimulationView(APIView):
    template_name = 'result.html'
    context = {}

    def post(self, request):
        value_lambda = request.POST.get('lambda')
        priority = request.POST.get('priority')
        fee_rate = request.POST.get('fee_rate')
        expected_waiting_time = Simulation1.waiting_times_estimate

        self.context = {
            'lambda': value_lambda, 'priority': priority, 'fee': fee_rate, 'expected_waiting_time': expected_waiting_time[int(priority)]
        }
        
        return render(request, self.template_name, {'data' : self.context})

def home (request):
    return render (request, 'home.html',{})

def calculator (request):
    return render (request, 'calculator.html',{})

def faq (request):
    return render (request, 'faq.html',{})

def graph (request):
    #test graph
    div_placehold = Simulation1.div
    context = {
        'div_placehold': Markup(div_placehold)
    }
    return render (request, 'graph.html', context)

def get_price(coin, currency):
    try:
        response = requests.get(URL.format(coin, currency)).json()
        return response
    except:
        return False

def bitcoinPrice(request):
        #while True:
    date_time = datetime.now()
    date_time = date_time.strftime("%d/%m/%Y %H:%M:%S")
    currentPrice = requests.get(URL.format("BTC", "AUD")).json()
    btc_price_range = {}

    datetime_today = date.today()
    date_today = str(datetime_today)
    date_10daysago = str(datetime_today - timedelta(days=10))

    api = ' https://api.coindesk.com/v1/bpi/historical/close.json?start=' + date_10daysago + '&end=' + date_today + '&index=[USD]' 
    try:
            response = requests.get(api, timeout=2)    # get api response data from coindesk based on date range supplied by user
            response.raise_for_status()            # raise error if HTTP request returned an unsuccessful status code.
            prices = response.json()    #convert response to json format
            btc_price_range = prices.get("bpi")   # filter prices based on "bpi" values only
    except requests.exceptions.ConnectionError as errc:  #raise error if connection fails
            raise ConnectionError(errc)
    except requests.exceptions.Timeout as errt:   # raise error if the request gets timed out without receiving a single byte
            raise TimeoutError(errt)
    except requests.exceptions.HTTPError as err:   # raise a general error if the above named errors are not triggered 
            raise SystemExit(err)

    df = pd.DataFrame(dict(
        dates = list(btc_price_range.keys()),
        cost = list(btc_price_range.values())
    ))
    fig = px.line(df, x="dates", y="cost", title="Transition of BTC Price for last 10 days") 
    div_placehold = plotly.io.to_html(fig, include_plotlyjs=False, full_html=False)

    context = {
          'price':btc_price_range,
          'cp':currentPrice ["AUD"],
          'dateTime': date_time,
          'div_placehold': Markup(div_placehold)
    }
    return render(request, 'bitcoinPrice.html', context)
   
