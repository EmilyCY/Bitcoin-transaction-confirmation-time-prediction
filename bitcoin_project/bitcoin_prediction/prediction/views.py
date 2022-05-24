from django.shortcuts import render
from rest_framework.views import APIView

from .populate_db import load_data_to_model
from .queueing_model_simulation import Simulation1, get_priority
from .estimating_waiting_time import EstimatingWaitingTime
import requests
from datetime import date, timedelta, datetime
from flask import Markup
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
URL = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}"

# Create your views here.
def main(request):
    return render(request, 'base.html')

def population(request):
    load_data_to_model(request)
    return render(request, 'base.html')

def test(request):
    return render(request, 'test.html')

class SimulationView(APIView):
    template_name = 'result.html'
    context = {}

    def post(self, request):
        num_of_priorities = int(request.POST.get('num_of_priorities'))
        fee_rate = float(request.POST.get('fee_rate'))

        # get lists of calculated waiting time from each model
        waiting_time_on_model = EstimatingWaitingTime.P_GROUP_WAITING_TIMES.get(num_of_priorities)
        expected_waiting_time = Simulation1.EXPECTED_WAITING_TIME.get(num_of_priorities)

        # decision of priority depending on fee rate
        feerate_range = Simulation1.P_GROUP_FEE_RATE_RANGE.get(num_of_priorities)
        priority = get_priority(fee_rate, feerate_range)

        # create graph
        p_list = []
        for i in range(1, num_of_priorities+1):
            p_list.append(f'Class {i}')
        col_name = ['priority', 'waiting_time', 'expected_waiting_time']
        df = pd.DataFrame(zip(p_list, waiting_time_on_model, expected_waiting_time), columns=col_name)
        data1 = go.Bar(x=df['priority'], y=df['waiting_time'], name='Waiting Time on Model')
        data2 = go.Bar(x=df['priority'], y=df['expected_waiting_time'], name='Expected Waiting Time on Simulation')
        layout = go.Layout(title='Comparison of Waiting time')
        fig = go.Figure(data=[data1, data2], layout=layout, layout_yaxis_range=[0, 40000])
        div_placehold = plotly.io.to_html(fig, include_plotlyjs=False, full_html=False)
        
        self.context = {
            'priority': priority,
            'fee': fee_rate,
            'waiting_time_on_model': round(waiting_time_on_model[priority-1], 2),
            'expected_waiting_time': round(expected_waiting_time[priority-1], 2),
            'div_placehold': Markup(div_placehold)
        }
        
        return render(request, self.template_name, {'data' : self.context})

#def home (request):
#    return render (request, 'home.html',{})

def calculator (request):
    return render (request, 'calculator.html',{})

def faq (request):
    return render (request, 'faq.html',{})

def graph (request):
    return render (request, 'graph.html', {})

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