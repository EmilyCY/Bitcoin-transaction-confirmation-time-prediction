from django.contrib import admin
from .models import Simulation, Transaction

# Register your models here.
admin.site.register(Transaction)
admin.site.register(Simulation)