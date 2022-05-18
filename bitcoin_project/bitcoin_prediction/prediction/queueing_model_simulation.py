#!/usr/bin/env python
# coding: utf-8

# # Queueing Model

# reference 
# 
# https://docs.python.org/3/library/queue.html
# 
# https://numpy.org/doc/stable/reference/random/generated/numpy.random.exponential.html

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import time
import queue as Q
from collections import deque
from collections import namedtuple as nt

from .models import Transaction
from sqlalchemy import create_engine
import plotly
import plotly.express as px

class Simulation1:
    # Data Loading
    # export 1000 data to test quickly
    engine = create_engine('postgresql://postgres:admin123@localhost:5432/transactions', echo=False)
    sql_query = 'SELECT * FROM transaction ORDER BY RANDOM() LIMIT 1000'
    data = pd.read_sql_query(sql_query, con = engine)
    
    """
    # loading all data from model to pandas dataframe
    queryset = Transaction.objects.values('index', 'inputs', 'outputs', 'trans_version', 'trans_size', 'trans_weight', 
                    'received_time', 'relay_node', 'locktime', 'trans_fee', 'confirmed_block_height', 'index_block_height',
                    'confirm_time', 'waiting_time', 'feerate', 'enter_block_height', 'waiting_block_num', 'valid_time',
                    'valid_block_height', 'valid_waiting', 'last_block_interval')
    data = pd.DataFrame(queryset)

    # load the data 
    data1 = pd.read_csv("TimetxinBlock621500.csv")
    data1.columns = ['index', 'inputs', 'outputs', 'trans_version', 'trans_size', 'trans_weight', 'received_time',
                    'relay_node', 'locktime', 'trans_fee', 'confirmed_block_height', 'index_block_height', 'confirm_time',
                    'waiting_time', 'feerate', 'enter_block_height', 'waiting_block_num', 'valid_time',
                    'valid_block_height', 'valid_waiting', 'last_block_interval']
    data2 = pd.read_csv("TimetxinBlock622000.csv")
    data2.columns = ['index', 'inputs', 'outputs', 'trans_version', 'trans_size', 'trans_weight', 'received_time',
                    'relay_node', 'locktime', 'trans_fee', 'confirmed_block_height', 'index_block_height', 'confirm_time',
                    'waiting_time', 'feerate', 'enter_block_height', 'waiting_block_num', 'valid_time',
                    'valid_block_height', 'valid_waiting', 'last_block_interval']
    data3 = pd.read_csv("TimetxinBlock622500.csv")
    data3.columns = ['index', 'inputs', 'outputs', 'trans_version', 'trans_size', 'trans_weight', 'received_time',
                    'relay_node', 'locktime', 'trans_fee', 'confirmed_block_height', 'index_block_height', 'confirm_time',
                    'waiting_time', 'feerate', 'enter_block_height', 'waiting_block_num', 'valid_time',
                    'valid_block_height', 'valid_waiting', 'last_block_interval']

    # combine the data into one dataframe
    data = pd.concat([data1, data2, data3], ignore_index=True)
    # data1.columns=['index','inputs','outputs','trans_version','trans_size','trans_weight','received_time','relay_node','locktime','trans_fee','confirmed_block_height','index_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num','valid_time','valid_block_height','valid_waiting','last_block_interval']
    print(data.shape)
    data = data.sort_values(by=['received_time'])
    data.head(20)

    max_block = data['waiting_block_num'].max()
    print(max_block)
    data['waiting_block_num'].describe()
    print(data['received_time'].max())
    """
    # input Parameters

    # lambda calculation - arrival rate 
    total_trans_num = len(data.index)
    print("Total number of transactions: ", total_trans_num)

    data_sort_by_receive = data.sort_values(by='received_time')
    first_arrive_time = float(data['received_time'].min())
    last_arrive_time = float(data['received_time'].max())
    q_lambda = float(total_trans_num) / (last_arrive_time - first_arrive_time)
    mean_interarrival_time = 1 / q_lambda
    print("lambda is: ", q_lambda)

    # mu - service rate
    service_time_mean = 600
    mu = 1 / service_time_mean
    print("Mu is: ", mu)

    # total time (seconds)
    simulation_time = last_arrive_time - first_arrive_time
    print("Total simulation time is: ", simulation_time)

    # mempool capacity
    trans_size = 535
    mempool_size = 300 * 1000000
    capacity = mempool_size / trans_size
    print("Mempool capacity is ", capacity, " transactions")

    # block size 
    block_groups = data.groupby(['confirmed_block_height'])['confirmed_block_height'].count()
    b = float(round(block_groups.mean()))
    print("Mean Block Size: ", b)

    # store feerates in a list to feed in the model later 
    feerates = data.feerate.tolist()

    # initiate results 
    results = []

    # ## Priority Groups Setup - feerate range calculation


    # This function is to calcutate the feerate boundary of each priority group

    WAIT_BLOCK_NUM_UPPER_BOUNDARY = [1, 3, 10]

    length = len(WAIT_BLOCK_NUM_UPPER_BOUNDARY)

    # this function return a list with the feerate boundaries for each priority group
    def calculate_feerate_for_priority_groups(data, upper_boundary, length):
        feerate_range = []
        transaction_counts = 0
        for i in range(length):
            transaction_counts = len(data[data['waiting_block_num'] <= upper_boundary[i]])
            boundary = data.feerate.nlargest(transaction_counts).iloc[-1]
            feerate_range.append(boundary)
        return feerate_range


    feerate_range = calculate_feerate_for_priority_groups(data, WAIT_BLOCK_NUM_UPPER_BOUNDARY, length)
    print("Feerate boundaries: ", feerate_range)

    # # M/M/1 Queueing Model
    # 
    # The data structure deque is selected becaused deque provides an O(1) time complexity for append and pop operations, so that system drlay can be minimised. 


    # initiate variables 
    transaction = nt('transaction',
                    ['received_time', 'feerate', 'confirm_time', 'entered_block_height', 'confirmed_block_height'])

    q1 = deque()
    q2 = deque()
    q3 = deque()
    q4 = deque()

    t = round(time.time())
    next_arrival = t
    next_confirm = next_arrival + round(np.random.exponential(service_time_mean))
    block_height = 620943

    # place holder for checking mempool size - not needed for given dataset
    # allocate transaction to different priority groups and populating the arrival time  

    i = 0
    while next_confirm <= t + simulation_time:
        while next_arrival < next_confirm and i < len(feerates):  # transactions come in before the next batch
            feerate = feerates[i]
            if feerate >= feerate_range[0]:
                q1.append(transaction(next_arrival, feerate, 0, block_height, 0))
            if (feerate >= feerate_range[1]) & (feerate < feerate_range[0]):
                q2.append(transaction(next_arrival, feerate, 0, block_height, 0))
            if (feerate >= feerate_range[2]) & (feerate < feerate_range[1]):
                q3.append(transaction(next_arrival, feerate, 0, block_height, 0))
            if feerate < feerate_range[2]:
                q4.append(transaction(next_arrival, feerate, 0, block_height, 0))
            next_arrival += round(np.random.exponential(1 / q_lambda))
            i += 1

        # batch processing with size b
        j = 0
        block_height = block_height + 1
        while q1 and j <= b:
            # - using popleft() to delete element from left end 
            q1[0] = q1[0]._replace(confirm_time=next_confirm)
            q1[0] = q1[0]._replace(confirmed_block_height=block_height)
            confirmed = q1.popleft()
            results.append(confirmed)
            j += 1
        while q2 and j <= b:
            q2[0] = q2[0]._replace(confirm_time=next_confirm)
            q2[0] = q2[0]._replace(confirmed_block_height=block_height)
            confirmed = q2.popleft()
            results.append(confirmed)
            j += 1
        while q3 and j <= b:
            q3[0] = q3[0]._replace(confirm_time=next_confirm)
            q3[0] = q3[0]._replace(confirmed_block_height=block_height)
            confirmed = q3.popleft()
            results.append(confirmed)
            j += 1
        while q4 and j <= b:
            q4[0] = q4[0]._replace(confirm_time=next_confirm)
            q4[0] = q4[0]._replace(confirmed_block_height=block_height)
            confirmed = q4.popleft()
            results.append(confirmed)
            j += 1

        # calculate next confirmation time 
        next_confirm += round(np.random.exponential(service_time_mean))

    results_df = pd.DataFrame(results, columns=transaction._fields)
    results_df = results_df.apply(pd.to_numeric)
    results_df['waiting_time'] = results_df['confirm_time'] - results_df['received_time']
    results_df['waited_block_num'] = results_df['confirmed_block_height'] - results_df['entered_block_height']
    results_df.head(50)


    # calculate Average wait time

    def calculate_mean_waiting_time(results_df, feerate_range):
        waiting_times = []
        for i in range(len(feerate_range)):
            if i == 0:
                df = results_df[results_df['feerate'] > feerate_range[i]]
                waiting_time_mean = df['waiting_time'].mean()
                waiting_times.append(waiting_time_mean)
            if i < len(feerate_range) - 1:
                df = results_df[results_df['feerate'].between(feerate_range[i + 1], feerate_range[i], inclusive="right")]
                waiting_time_mean = df['waiting_time'].mean()
                waiting_times.append(waiting_time_mean)
            if i == len(feerate_range) - 1:
                df = results_df[results_df['feerate'] <= feerate_range[i]]
                waiting_time_mean = df['waiting_time'].mean()
                waiting_times.append(waiting_time_mean)
        return waiting_times

    waiting_times_estimate = calculate_mean_waiting_time(results_df, feerate_range)
    waiting_times_actual = calculate_mean_waiting_time(data, feerate_range)

    print("mean waiting times for each priority group (from high to low) are: ", waiting_times_estimate)
    print("mean waiting times for each priority group (from high to low) in raw data are: ", waiting_times_actual)


    # example of generating graph
    test_df = data['received_time']
    fig = px.histogram(test_df, x="received_time", title='test histogram')
    div = plotly.io.to_html(fig, include_plotlyjs=False, full_html=False)
