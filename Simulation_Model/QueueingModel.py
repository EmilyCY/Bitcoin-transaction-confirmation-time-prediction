#!/usr/bin/env python
# coding: utf-8

# # Queueing Model

# reference 
# 
# https://docs.python.org/3/library/queue.html
# 
# https://numpy.org/doc/stable/reference/random/generated/numpy.random.exponential.html

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import time
from collections import deque
from collections import namedtuple as nt


# In[2]:


# import the math model 
get_ipython().run_line_magic('run', '../Wait_Times_Math_Model/QueueWaitTimes.ipynb')


# ## Data Loading 

# In[3]:


# load the data 
data1 = pd.read_csv("TimetxinBlock621500.csv")
data1.columns=['index','inputs','outputs','trans_version','trans_size','trans_weight','received_time','relay_node','locktime','trans_fee','confirmed_block_height','index_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num','valid_time','valid_block_height','valid_waiting','last_block_interval']
data2 = pd.read_csv("TimetxinBlock622000.csv")
data2.columns=['index','inputs','outputs','trans_version','trans_size','trans_weight','received_time','relay_node','locktime','trans_fee','confirmed_block_height','index_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num','valid_time','valid_block_height','valid_waiting','last_block_interval']
data3 = pd.read_csv("TimetxinBlock622500.csv")
data3.columns=['index','inputs','outputs','trans_version','trans_size','trans_weight','received_time','relay_node','locktime','trans_fee','confirmed_block_height','index_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num','valid_time','valid_block_height','valid_waiting','last_block_interval']


# combine the data into one dataframe
data = pd.concat([data1, data2, data3], ignore_index = True)
# data1.columns=['index','inputs','outputs','trans_version','trans_size','trans_weight','received_time','relay_node','locktime','trans_fee','confirmed_block_height','index_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num','valid_time','valid_block_height','valid_waiting','last_block_interval']
print(data.shape)
data = data.sort_values(by=['received_time'])
data.head(20)


# ## Parameters - User inputs

# In[4]:


# Default block size if not specified 
block_groups = data.groupby(['confirmed_block_height'])['confirmed_block_height'].count()
mean_block_size = float(round(block_groups.mean()))

# Replace with user input
b=mean_block_size
print("Block Size: ", b)

# Number of priority groups
PGROUP_NUM=4

#feerate range 
def get_boundary(pgroup_num):
    boundaries={2:[1], 4:[1,3,10] , 6:[1,2,4,8,23], 8:[1,2,4,7,13,23,50]}
    return boundaries.get(pgroup_num,[1,3,10])

WAIT_BLOCK_NUM_UPPER_BOUNDARY = get_boundary(PGROUP_NUM)
print(WAIT_BLOCK_NUM_UPPER_BOUNDARY)
    


# ## Priority Groups Setup - feerate range calculation 

# In[5]:


length=len(WAIT_BLOCK_NUM_UPPER_BOUNDARY)

# this function returns a list with the feerate boundaries for each priority group
def calculate_feerate_for_priority_groups(data, upper_boundary):
    feerate_range = []
    feerate_range.append(data['feerate'].max())
    transaction_counts=0
    for i in range(length):
        transaction_counts = len(data[data['waiting_block_num']<=upper_boundary[i]])
        boundary = data.feerate.nlargest(transaction_counts).iloc[-1]
        feerate_range.append(boundary)
    feerate_range.append(0)
    return feerate_range
            

feerate_range=calculate_feerate_for_priority_groups(data, WAIT_BLOCK_NUM_UPPER_BOUNDARY)
print("Feerate boundaries: ",feerate_range)


# ## Parameters - fixed

# In[6]:


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

# In[7]:


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
results_df.head(50)


# In[8]:


#calculate average wait time 

def calculate_mean_waiting_time(results_df, feerate_range):
    waiting_times=[]
    for i in range(len(feerate_range)):
        if i<len(feerate_range)-1:
            df=results_df[results_df['feerate'].between(feerate_range[i+1],feerate_range[i],inclusive="right")]
            waiting_time_mean=df['waiting_time'].mean()
            waiting_times.append(waiting_time_mean)
    return waiting_times

waiting_times_estimate=calculate_mean_waiting_time(results_df, feerate_range)
waiting_times_actual=calculate_mean_waiting_time(data, feerate_range)

print("mean waiting times for each priority group (from high to low) are: ", waiting_times_estimate)
print("mean waiting times for each priority group (from high to low) in raw data are: ", waiting_times_actual)        
   


# In[ ]:




