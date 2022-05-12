from django import forms

class SimulationForm(forms.Form):
    priority = forms.DateField(widget=forms.DateInput(attrs={'type': 'number'}))
    fee = forms.DateField(widget=forms.DateInput(attrs={'type': 'number'}))
