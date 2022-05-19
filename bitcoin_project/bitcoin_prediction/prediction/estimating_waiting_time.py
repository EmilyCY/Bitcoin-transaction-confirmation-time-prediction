import pandas
from scipy.optimize import newton
from .populate_db import load_data

P_GROUP_BOUNDS = [1,3,10]
#HEADER_NAMES = ['trans_size','trans_weight','received_time','trans_fee','confirmed_block_height','confirm_time','waiting_time','feerate','enter_block_height','waiting_block_num']

class EstimatingWaitingTime:
    test = 1
    dataFrame = load_data()

    dataFrame = dataFrame[dataFrame['waiting_time'] >= 0] # Remove any rows with negative values for waiting_time
    print("Transaction Count: ", len(dataFrame))

    # Block Size
    block_groups = dataFrame.groupby(['confirmed_block_height'])['confirmed_block_height'].count()
    mean_block_size = float(round(block_groups.mean()))
    print("Mean Block Size: ", mean_block_size)

    # Fee Rate Priority Range
    def calculate_feerate_for_priority_groups(data, upper_boundary):
        feerate_range = []
        transaction_counts = 0
        feerate_range.append(data['feerate'].max())
        for i in range(len(P_GROUP_BOUNDS)):
            transaction_counts = len(data[data['waiting_block_num'] <= upper_boundary[i]])
            #boundary = data['fee_rate'].nlargest(transaction_counts).iloc[-1]
            boundary = data['feerate'].tail(transaction_counts).iloc[0]
            feerate_range.append(boundary)
        return feerate_range

    p_groups_feerate_range = calculate_feerate_for_priority_groups(dataFrame.sort_values('feerate'), P_GROUP_BOUNDS)
    p_groups_feerate_range.append(0.0)
    print("Fee Rate Priority Range: ", p_groups_feerate_range)

    # Arrival Rates (Lambda) - Priority
    raw_wait_times = []
    p_groups_lambda = []
    transaction_count = len(dataFrame)
    received_time_max = dataFrame['received_time'].max()
    received_time_min = dataFrame['received_time'].min()

    for current, next in zip(p_groups_feerate_range,p_groups_feerate_range[1:]):
        p_df = dataFrame[(dataFrame['feerate'] <= current) & (dataFrame['feerate'] > next)]
        p_transaction_count = len(p_df)
        #p_lambda = float(p_transaction_count) / (float(p_df['received_time'].max()) - float(p_df['received_time'].min()))
        p_lambda = float(p_transaction_count) / (received_time_max - received_time_min)
        p_groups_lambda.append(p_lambda)
        raw_wait_times.append(p_df['waiting_time'].mean())

        print("Priority Group " + str(p_groups_feerate_range.index(current)+1))
        print("Transaction Count: " + str(p_transaction_count) + ", Raw Wait Time (Mean): " + str(p_df['waiting_time'].mean()))
        print("Feerate Min: " + str(float(p_df['feerate'].min())) + ", Max: " + str(float(p_df['feerate'].max())))
        print("Lambda: " + str(p_lambda))

    print("\nSum Of All Lambda: ", sum(p_groups_lambda))

    # Service Rate (Mu)
    service_time = 600
    mu = 1/service_time # = 0.0016666666666666668
    #mu = (1/service_time)*mean_block_size # = 3.776666666666667
    print("Mu: ", mu)

    # Validation Of Z Using Newton Method (Mine Vs SciPy)
    my_p_group_z = []
    sciPy_p_group_z = []
    lambda_sum = 0.0

    def newtonMethod(lam, m_u, block_size, x0, epsilon):
        fx = lambda x: lam*(1 - x) - m_u*x*(1 - x**block_size)
        dfx = lambda x: m_u*(block_size*x**block_size + x**block_size - 1) - lam
        while True:
            x1 = x0 - fx(x0) / dfx(x0)
            t = abs(x1 - x0)
            if t < epsilon:
                break
            x0 = x1
        return x0

    def sciPyNewton(lam, m_u, block_size, x0, epsilon, max_iteration):
        fx = lambda x: lam*(1 - x) - m_u*x*(1 - x**block_size)
        #dfx = lambda x: m_u*(block_size*x**block_size + x**block_size - 1) - lam
        #return newton(fx, x0, fprime=dfx, args=(), tol=epsilon, maxiter=max_iteration, fprime2=None)
        return newton(fx, x0, fprime=None, args=(), tol=epsilon, maxiter=max_iteration, fprime2=None)

    for i in range(len(p_groups_lambda)):
        lambda_sum += p_groups_lambda[i]
        my_p_group_z.append(newtonMethod(lambda_sum, mu, mean_block_size, 0, 1e-10))
        sciPy_p_group_z.append(sciPyNewton(lambda_sum, mu, mean_block_size, 0, 1e-10, 500))

    for i in range(len(my_p_group_z)):
        print("Priority Group " + str(i+1))
        print("My Z: " + str(my_p_group_z[i]) + ", SciPy Z: " + str(sciPy_p_group_z[i]))

    # Wait Times Using Z
    prev_transaction_in_queue = 0.0
    p_group_response_time = []

    for i in range(len(p_groups_lambda)):
        temp = sciPy_p_group_z[i] / (1 - sciPy_p_group_z[i]) # L(y) = z(x) / (1 - z(x))
        transaction_in_queue = temp - prev_transaction_in_queue # L(x) = L(y) - L(y-1)
        prev_transaction_in_queue = temp

        #transaction_in_queue = my_p_group_z[i] / (1 - my_p_group_z[i]) - prev_transaction_in_queue # L(x) = (z(x) / (1 - z(x))) - L(x-1)
        #prev_transaction_in_queue = transaction_in_queue

        response_time = transaction_in_queue / p_groups_lambda[i] # W(x) = L(x) / Lambda(x)

        p_group_response_time.append(response_time)

        print("Priority Group " + str(i+1))
        print("Average Transaction In Queue (L): ", transaction_in_queue)
        print("Average Response Time In Queue (W): " + str(response_time))
            