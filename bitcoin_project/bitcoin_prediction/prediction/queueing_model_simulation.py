#!/usr/bin/env python
# coding: utf-8

# # Queueing Model

# reference 
# 
# https://docs.python.org/3/library/queue.html
# 
# https://numpy.org/doc/stable/reference/random/generated/numpy.random.exponential.html

import imp
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
from .populate_db import load_data
import plotly
import plotly.express as px

P_GROUP_BLOCK_INTERVAL_DICTIONARY = {
    2 : [1],
    4 : [1,3,10],
    6 : [1,2,4,8,23],
    8 : [1,2,4,7,13,23,50]
}

# this function returns a list with the feerate boundaries for each priority group
def calculate_feerate_for_priority_groups(data, upper_boundary):
    feerate_range = []
    feerate_range.append(data['feerate'].max())
    transaction_counts=0
    for i in range(len(upper_boundary)):
        transaction_counts = len(data[data['waiting_block_num']<=upper_boundary[i]])
        boundary = data.feerate.nlargest(transaction_counts).iloc[-1]
        feerate_range.append(boundary)
    feerate_range.append(0)
    return feerate_range

def calculate_mean_waiting_time(results_df, feerate_range):
    waiting_times=[]
    for i in range(len(feerate_range)):
        if i<len(feerate_range)-1:
            df=results_df[results_df['feerate'].between(feerate_range[i+1],feerate_range[i],inclusive="right")]
            waiting_time_mean=df['waiting_time'].mean()
            waiting_times.append(waiting_time_mean)
    return waiting_times

def get_priority(user_input_fee_rate, feerate_range):
    priority = 0
    for index in range(1, len(feerate_range)):
        if user_input_fee_rate >= feerate_range[index]:
            priority = index
            return priority


class Simulation1:
    # Data Loading
    # export 1000 data to test quickly
    #engine = create_engine('postgresql://postgres:admin123@localhost:5432/transactions', echo=False)
    #sql_query = 'SELECT * FROM transaction ORDER BY RANDOM() LIMIT 1000'
    #data = pd.read_sql_query(sql_query, con = engine)

    # Variables used in view.py    
    EXPECTED_WAITING_TIME = {}
    P_GROUP_FEE_RATE_RANGE = {}
    pgroup_num = 2
    priority = 1
    user_input_fee_rate = 0
    
    #try:
    #    Transaction.objects.exists()
    data = load_data()

    # input Parameters
    # Default block size if not specified 
    block_groups = data.groupby(['confirmed_block_height'])['confirmed_block_height'].count()
    mean_block_size = float(round(block_groups.mean()))

    # Replace with user input
    b=mean_block_size
    print("Block Size: ", b)

    #feerate range 
    def get_boundary(pgroup_num):
        boundaries={2:[1], 4:[1,3,10] , 6:[1,2,4,8,23], 8:[1,2,4,7,13,23,50]}
        return boundaries.get(pgroup_num)

    WAIT_BLOCK_NUM_UPPER_BOUNDARY = get_boundary(pgroup_num)
    print(WAIT_BLOCK_NUM_UPPER_BOUNDARY)

    # ## Priority Groups Setup - feerate range calculation
    
    feerate_range=calculate_feerate_for_priority_groups(data, WAIT_BLOCK_NUM_UPPER_BOUNDARY)
    print("Feerate boundaries: ",feerate_range)

    for index in range(1, len(feerate_range)):
        if user_input_fee_rate >= feerate_range[index]:
            priority = index
    
    print("current priority", priority)
    
                
    # lambda calculation - arrival rate 
    total_trans_num = len(data.index)
    print("Total number of transactions: ", total_trans_num)

    data_sort_by_receive = data.sort_values(by='received_time')
    first_arrive_time=float(data['received_time'].min())
    last_arrive_time=float(data['received_time'].max())
    q_lambda=float(total_trans_num)/(last_arrive_time-first_arrive_time)
    mean_interarrival_time=1/q_lambda
    print("lambda is: ", q_lambda)

    # mu - service rate
    service_time_mean=600
    mu = 1/service_time_mean
    print("Mu is: ", mu)

    # total simulation time (seconds)
    simulation_time = last_arrive_time-first_arrive_time
    print("Total simulation time is: ", simulation_time)

    # mempool capacity
    trans_size=535
    mempool_size=300*1000000
    capacity = mempool_size/trans_size
    print("Mempool capacity is ", capacity, " transactions")

    # store feerates in a list to feed in the model later 
    feerates=data.feerate.tolist()

    # initiate results 
    results=[]

    # # M/Mb/1 Queueing Model with Priority Groups Based on Transaction Fees
    # 
    # The data structure deque is selected becaused deque provides an O(1) time complexity for append and pop operations, so that system drlay can be minimised. 

    # create named tuple to store single transaction information 
    transaction=nt('transaction',['received_time','feerate','confirm_time','enter_block_height','confirmed_block_height'])

    #initialise the groups 
    deques=[]
    for n in range(len(feerate_range)-1):
        queue=deque()
        deques.append(queue)

    #t=round(time.time())
    t=data.received_time.min()  
    next_arrival=t
    next_confirm=next_arrival+round(np.random.exponential(service_time_mean))
    block_height=data.enter_block_height.min()


    ## place holder for checking mempool size - not needed for given dataset
    # allocate transaction to different priority groups and populating the arrival time  

    i=0    
    while next_confirm <= t + simulation_time:
        while (next_arrival < next_confirm and i<len(feerates)):  # transactions come in before the next batch
            feerate = feerates[i]
            for k in range(len(deques)):
                if (feerate>feerate_range[k+1]) & (feerate<=feerate_range[k]):  
                    deques[k].append(transaction(next_arrival,feerate,0,block_height,0))      
            next_arrival += round(np.random.exponential(1/q_lambda))
            i+=1
            
        # batch processing with size b
        j=0
        block_height = block_height + 1
        for q in deques:
            while q and j<=b:
                # - using popleft() to delete element from left end 
                q[0] = q[0]._replace(confirm_time=next_confirm)
                q[0] = q[0]._replace(confirmed_block_height=block_height)
                confirmed = q.popleft()
                results.append(confirmed)
                j+=1
    
        # calculate next confirmation time 
        next_confirm += round(np.random.exponential(service_time_mean))

    for q in deques:
        q.clear()
        
    results_df=pd.DataFrame(results,columns=transaction._fields)
    results_df=results_df.apply(pd.to_numeric)
    results_df['waiting_time']=results_df['confirm_time']-results_df['received_time']
    results_df['waited_block_num']=results_df['confirmed_block_height']-results_df['enter_block_height']



    waiting_times_estimate=calculate_mean_waiting_time(results_df, feerate_range)
    waiting_times_actual=calculate_mean_waiting_time(data, feerate_range)

    print("mean waiting times for each priority group (from high to low) are: ", waiting_times_estimate)
    print("mean waiting times for each priority group (from high to low) in raw data are: ", waiting_times_actual)        
    
    for key, value in P_GROUP_BLOCK_INTERVAL_DICTIONARY.items():
        feerate_range = calculate_feerate_for_priority_groups(data, value)
        p_waiting_times = calculate_mean_waiting_time(results_df, feerate_range)
        EXPECTED_WAITING_TIME[key] = p_waiting_times
        P_GROUP_FEE_RATE_RANGE[key] = feerate_range

    print("waiting time", EXPECTED_WAITING_TIME)
    print("feerate range", P_GROUP_FEE_RATE_RANGE)
    # example of generating graph
    #test_df = data['received_time']
    #fig = px.histogram(test_df, x="received_time", title='test histogram')
    #div = plotly.io.to_html(fig, include_plotlyjs=False, full_html=False)
        
    #except Transaction.DoesNotExist:
    #    print("No data in transaction relation")
    #except :
    #    print("No data in transaction relation")