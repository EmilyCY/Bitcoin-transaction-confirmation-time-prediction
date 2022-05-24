import pandas
from scipy.optimize import newton

P_GROUP_SIZE = 2
P_GROUP_BLOCK_INTERVAL_DICTIONARY = {
    2 : [1],
    4 : [1,3,10],
    6 : [1,2,4,8,23],
    8 : [1,2,4,7,13,23,50]
}

def calculate_feerate_for_priority_groups(data, upper_boundary):
    feerate_range = []
    transaction_counts = 0
    feerate_range.append(data['fee_rate'].max())
    for i in range(len(upper_boundary)):
        transaction_counts = len(data[data['no_block_confirm'] <= upper_boundary[i]])
        boundary = data['fee_rate'].tail(transaction_counts).iloc[0]
        feerate_range.append(boundary)
    feerate_range.append(0.0)
    return feerate_range

def calculate_lambda_for_priority_groups(data, feerate_range):
    p_groups_lambda = []
    received_time_max = data['received_time'].max()
    received_time_min = data['received_time'].min()
    for current, next in zip(feerate_range,feerate_range[1:]):
        p_df = data[(data['fee_rate'] <= current) & (data['fee_rate'] > next)]
        p_transaction_count = len(p_df)
        p_lambda = float(p_transaction_count) / (received_time_max - received_time_min)
        p_groups_lambda.append(p_lambda)
    return p_groups_lambda

def NewtonMethod(lam, m_u, block_size, x0, epsilon):
    fx = lambda x: lam*(1 - x) - m_u*x*(1 - x**block_size)
    dfx = lambda x: m_u*(block_size*x**block_size + x**block_size - 1) - lam
    while True:
        x1 = x0 - fx(x0) / dfx(x0)
        t = abs(x1 - x0)
        if t < epsilon:
            break
        x0 = x1
    return x0

def SciPyNewton(lam, m_u, block_size, x0, epsilon, max_iteration):
    fx = lambda x: lam*(1 - x) - m_u*x*(1 - x**block_size)
    #dfx = lambda x: m_u*(block_size*x**block_size + x**block_size - 1) - lam
    #return newton(fx, x0, fprime=dfx, args=(), tol=epsilon, maxiter=max_iteration, fprime2=None)
    return newton(fx, x0, fprime=None, args=(), tol=epsilon, maxiter=max_iteration, fprime2=None)

def calculate_z_priority(lambda_priority_group, mu, mean_block_size):
    my_p_group_z = []
    sciPy_p_group_z = []
    lambda_sum = 0.0
    for i in range(len(lambda_priority_group)):
        lambda_sum += lambda_priority_group[i]
        my_p_group_z.append(NewtonMethod(lambda_sum, mu, mean_block_size, 0, 1e-10))
        sciPy_p_group_z.append(SciPyNewton(lambda_sum, mu, mean_block_size, 0, 1e-10, 500))
    #return my_p_group_z
    return sciPy_p_group_z

def calculate_wait_time_for_priority_groups(p_group_lambda, p_group_z):
    prev_transaction_in_queue = 0.0
    p_group_response_time = []
    for i in range(len(p_group_lambda)):
        temp = p_group_z[i] / (1 - p_group_z[i])
        transaction_in_queue = temp - prev_transaction_in_queue
        prev_transaction_in_queue = temp
        response_time = transaction_in_queue / p_group_lambda[i]
        p_group_response_time.append(response_time)
    return p_group_response_time

class EstimatingWaitingTime:
    P_GROUP_WAITING_TIMES = {}

    try:
        COLS_TO_USE = [4,5,6,9,10,12,13,14,15,16]
        HEADER_NAMES = ['size','weight','received_time','fee','confirmed_block_height','confirm_time','waiting_time','fee_rate','enter_block_height','no_block_confirm']
        d1 = pandas.read_csv('TimetxinBlock621500.csv', usecols=COLS_TO_USE, names=HEADER_NAMES)
        d2 = pandas.read_csv('TimetxinBlock622000.csv', usecols=COLS_TO_USE, names=HEADER_NAMES)
        d3 = pandas.read_csv('TimetxinBlock622500.csv', usecols=COLS_TO_USE, names=HEADER_NAMES)
        dataFrame = pandas.concat([d1, d2, d3])

        dataFrame = dataFrame[dataFrame['waiting_time'] >= 0] # Remove any rows with negative values for waiting_time

        block_groups = dataFrame.groupby(['confirmed_block_height'])['confirmed_block_height'].count()
        mean_block_size = float(round(block_groups.mean()))
        service_time = 600
        mu = 1/service_time

        for key, value in P_GROUP_BLOCK_INTERVAL_DICTIONARY.items():
            feerate_range = calculate_feerate_for_priority_groups(dataFrame.sort_values('fee_rate'), value)
            p_lambda = calculate_lambda_for_priority_groups(dataFrame, feerate_range)
            p_z = calculate_z_priority(p_lambda, mu, mean_block_size)
            p_wait_time = calculate_wait_time_for_priority_groups(p_lambda, p_z)
            P_GROUP_WAITING_TIMES[key] = p_wait_time

        #print("Wait Times For 4 Priority Groups:", P_GROUP_WAITING_TIMES.get(4))

    except :
        print("No data in transaction relation")
                