from .models import Transaction
import matplotlib.pyplot as plt
import pandas as pd

def cal_waiting_time():
    queryset = Transaction.objects.values('waiting_time_of_transaction')

    waiting_time = pd.DataFrame(queryset)
    average_waiting_time = waiting_time.mean()

    return average_waiting_time