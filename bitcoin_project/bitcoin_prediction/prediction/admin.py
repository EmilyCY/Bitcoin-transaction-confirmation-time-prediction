from django.contrib import admin
from .models import Transaction, Simulation

# Register your models here.
admin.site.register(Transaction)
admin.site.register(Simulation)