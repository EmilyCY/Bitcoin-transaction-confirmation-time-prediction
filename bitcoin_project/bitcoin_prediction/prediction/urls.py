from django.urls import path
from . import views
from .views import SimulationView

urlpatterns = [
    path("main/", views.main, name="main"),
    path('main/bitcoinPrice/', views.bitcoinPrice, name = 'bitcoinPrice'),
    path('main/calculator/', views.calculator, name = 'calculator'),
    path('main/faq/', views.faq, name = 'faq'),
    path('main/graph/', views.graph, name = 'graph'),
    path('main/result/', views.SimulationView.as_view(), name='result'),

    path("population/", views.population, name="population"),
    path('main/test/', views.test, name='test'),
]