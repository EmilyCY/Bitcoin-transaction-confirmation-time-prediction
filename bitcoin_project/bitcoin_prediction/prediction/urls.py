from django.urls import path
from . import views
from .views import SimulationView

urlpatterns = [
    path("main/", views.main, name="main"),
    path("population/", views.population, name="population"),
    path('main/simulation/<int:priority>/<int:fee>', SimulationView.as_view(), name='simulation'),
    
    path('main/test/', views.test, name='test'),
    path('main/test_result', SimulationView.as_view(), name='test_result'),
]