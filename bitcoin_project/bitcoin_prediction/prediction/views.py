from django.http import Http404
from django.shortcuts import render
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Simulation
from .serializers import SimulationSerializer
from .forms import SimulationForm

from .populate_db import load_data
from .test_method import cal_waiting_time

# Create your views here.
def main(request):
    return render(request, 'base.html')

def population(request):
    load_data(request)
    return render(request, 'base.html')

def test(request):
    return render(request, 'test.html')

class SimulationView(APIView):
    def get(self, request, priority, fee):
        #example of getting inputs and sending json about it
        waiting_time = cal_waiting_time()

        return Response(
            {
            'priority': priority,
            'fee': fee,
            'waiting_time': waiting_time
            }
        )
    
    def post(self, request):
        priority = request.POST.get('priority')
        fee_rate = request.POST.get('fee_rate')
        waiting_time = cal_waiting_time()
        #input_form = SimulationForm(request.POST or None)

        return Response(
            {
            'priority': priority,
            'fee': fee_rate,
            'waiting_time': waiting_time
            }
        )