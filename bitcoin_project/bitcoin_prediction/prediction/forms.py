from django import forms

class SimulationForm(forms.Form):
    priority = forms.IntegerField(widget=forms.DateInput(attrs={'type': 'number'}))
    fee = forms.FloatField(widget=forms.DateInput(attrs={'type': 'number'}))
