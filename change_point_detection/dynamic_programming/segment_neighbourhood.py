import os, math, sys, datetime
import numpy as np
import pandas as pd

sys.path.append("../../import_scripts/")
import plot_procedures, time_series, datetime_procedures
from time_series import TimeSeries

#PARAMETERS
dt_start, dt_end = datetime.datetime(2015, 12, 1), datetime.datetime(2015, 12, 7)
metric = "loss"
min_fraction_of_measures = 0.85
max_segments = 10 #not used in O(n**2) solution
min_segment_len = 10
#cost_type = "mse"
#cost_type = "likelihood_normal"
#cost_type = "likelihood_exponential"
cost_type = "likelihood_poisson"
penalization_type = "aic"
#penalization_type = "sic"
#penalization_type = "hannan_quinn"

target_year, target_month = dt_start.year, dt_start.month
date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def penalization(n, k):
	if penalization_type == "aic": return 0.1*k
	elif penalization_type == "sic": return 2*np.log(n)*k
	elif penalization_type == "hannan_quinn": return 2*np.log(np.log(n))*k
def penalization_linear(n):
	if penalization_type == "aic": return 2
	elif penalization_type == "sic": return 2*np.log(n)
	elif penalization_type == "hannan_quinn": return 2*np.log(np.log(n))

def get_mean(i, j):
	return np.float(prefix_sum[j] - prefix_sum[i-1])/(j-i+1)

def segment_is_degenerate(i, j):
	if (same_left[j] >= (j-i+1)): return True
	return False

def calc_same_left(data):
	global same_left
	n = len(data)
	same_left = np.zeros(n+1)
	same_left[1] = 1
	for i in xrange(2, n+1): 
		if data[i-1-1] == data[i-1]: same_left[i] = 1 + same_left[i-1]
		else: same_left[i] = 1

def calc_prefix_sum(data):
	global prefix_sum
	n = len(data)
	prefix_sum = np.zeros(n+1)
	prefix_sum[0] = 0
	for i in xrange(1, n+1): prefix_sum[i] = prefix_sum[i-1] + data[i-1]

def calc_mse_matrix(data):
	global mse_mat
	n = len(data)
	mse_mat = np.zeros(shape = (n+1, n+1))
	for i in xrange(1, n+1):
		mse_mat[i][i] = 0
		for j in xrange(i+1, n+1):
			mse_mat[i][j] = mse_mat[i][j-1] + np.float(j-i)/(j-i+1)*(data[j-1] - get_mean(i, j-1))**2

def calc_normal_log_likelihood_matrix(data):
	global normal_log_likelihood_mat 
	n = len(data)
	normal_log_likelihood_mat = np.zeros(shape = (n+1, n+1))
	for i in xrange(1, n+1):
		for j in xrange(i+1, n+1):
			if (segment_is_degenerate(i, j)): continue
			squared_std = mse_mat[i][j]
			normal_log_likelihood_mat[i][j] = -0.5*(j-i+1)*np.log(2*np.pi*squared_std) - 0.5*(j-i+1)

def calc_exponential_log_likelihood_matrix(data):
	global exponential_log_likelihood_mat 
	n = len(data)
	exponential_log_likelihood_mat = np.zeros(shape = (n+1, n+1))
	for i in xrange(1, n+1):
		for j in xrange(i+1, n+1):
			if (segment_is_degenerate(i, j)): continue
			lmbd = np.float(j-i+1)/(prefix_sum[j] - prefix_sum[i-1])
			exponential_log_likelihood_mat[i][j] = (j-i+1)*np.log(lmbd) - lmbd*(prefix_sum[j] - prefix_sum[i-1])

def calc_prefix_sum_log_factorial(data):
	global prefix_sum_log_factorial_mat
	n = len(data)
	prefix_sum_log_factorial_mat = np.zeros(shape = n+1)
	for i in xrange(1, n+1): prefix_sum_log_factorial_mat[i] = math.log(math.factorial(int(data[i-1]*100))) + prefix_sum_log_factorial_mat[i-1]

def calc_poisson_log_likelihood_matrix(data):
	global poisson_log_likelihood_mat
	n = len(data)
	poisson_log_likelihood_mat = np.zeros(shape = (n+1, n+1))
	for i in xrange(1, n+1):
		for j in xrange(i+1, n+1):
			if (segment_is_degenerate(i, j)): continue
			lmbd = float(prefix_sum[j] - prefix_sum[i-1])/(j-i+1)
			poisson_log_likelihood_mat[i][j] = -(j-i+1)*lmbd + (prefix_sum[j] - prefix_sum[i-1])*math.log(lmbd) - (prefix_sum_log_factorial_mat[j] - prefix_sum_log_factorial_mat[i-1])

def segment_cost(i, j):
	#segment has only one value: degenerate distribution
	if ("likelihood" in cost_type) and segment_is_degenerate(i, j): return (-2*np.log(1), "likelihood_degenerate")

	if cost_type == "mse": return (2*mse_mat[i][j], "mse")
	elif cost_type == "likelihood_normal": return (-2*normal_log_likelihood_mat[i][j], "likelihood_normal")
	elif cost_type == "likelihood_exponential": return (-2*exponential_log_likelihood_mat[i][j], "likelihood_exponential")
	elif cost_type == "likelihood_poisson": return (-2*poisson_log_likelihood_mat[i][j], "likelihood_poisson")

def write_change_points(change_points, segment_type, ts, out_file_path):
	file = open(out_file_path + "_change_points.csv", "w")
	file.write("change_point\n")
	for cp in change_points: file.write(str(ts.x[cp-1]) + "\n")
	file.close()

	file = open(out_file_path + "_segment_type.csv", "w")
	file.write("segment_type,left_point,right_point\n")
	for p in segment_type: file.write(str(p[0]) + "," + str(ts.x[p[1]-1]) + "," + str(ts.x[p[2]-1]) + "\n")
	file.close()

def segment_neighbourhood(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric, dt_start, dt_end)
	ts_compressed = time_series.get_compressed(ts)
	
	n = len(ts_compressed.y)
	calc_same_left(ts_compressed.y)
	calc_prefix_sum(ts_compressed.y)
	calc_mse_matrix(ts_compressed.y)
	if cost_type == "likelihood_exponential": calc_exponential_log_likelihood_matrix(ts_compressed.y)
	elif cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_compressed.y)
	elif cost_type == "likelihood_poisson":
		calc_prefix_sum_log_factorial(ts_compressed.y)
		calc_poisson_log_likelihood_matrix(ts_compressed.y)
		
	#calculate dp
	dp = np.zeros(shape = (max_segments+1, n+1))	
	for i in xrange(1, n+1): dp[0][i] = float("inf")
	for n_segments in xrange(1, max_segments+1):
		print n_segments
		for i in xrange(1, n+1):
			dp[n_segments][i] = float("inf")
			for j in xrange(1, i - min_segment_len+1 + 1):
				if segment_is_degenerate(j, i): continue 
				dp[n_segments][i] = min(dp[n_segments][i], dp[n_segments-1][j-1] + segment_cost(j, i)[0])
	
	#get best number of segments
	best_n_segments = 1
	for n_segments in xrange(2, max_segments+1):
		if dp[n_segments][n] + penalization(n, n_segments) <= dp[best_n_segments][n] + penalization(n, best_n_segments):
			best_n_segments = n_segments

	#backtrack: get change points
	segment_type, change_points = [], []
	i, n_segments = n, best_n_segments
	while n_segments > 1:
		for j in range(1, i - min_segment_len+1 + 1):
			if segment_is_degenerate(j, i): continue 
			if np.isclose(dp[n_segments][i], dp[n_segments-1][j-1] + segment_cost(j, i)[0]):
				segment_type.append((segment_cost(j, i)[1], j, i))
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				n_segments -= 1
				break
	if (len(change_points) > 0) and (change_points[-1] > 1): segment_type.append((segment_cost(1, change_points[-1]-1)[1], 1, change_points[-1]-1))
	
	write_change_points(change_points, segment_type, ts_compressed, out_file_path)
			
	dt_cp = []
	for cp in change_points: dt_cp.append(ts_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path + ".png", ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp)

"""
can only be used on penalization(n, k) = f(n)*k
"""
def segment_neighbourhood_linear_penalization(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric, dt_start, dt_end)
	ts_compressed = time_series.get_compressed(ts)

	n = len(ts_compressed.y)
	calc_same_left(ts_compressed.y)
	calc_prefix_sum(ts_compressed.y)
	calc_mse_matrix(ts_compressed.y)
	if cost_type == "likelihood_exponential": calc_exponential_log_likelihood_matrix(ts_compressed.y)
	elif cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_compressed.y)

	#calculate dp
	dp = np.zeros(n+1)	
	for i in xrange(1, n+1): dp[i] = float("inf")
	for i in xrange(1, n+1):
		dp[i] = float("inf")
		for j in xrange(1, i - min_segment_len+1 + 1): 
			if segment_is_degenerate(j, i): continue 
			dp[i] = min(dp[i], dp[j-1] + segment_cost(j, i)[0] + penalization_linear(n))
	
	#backtrack: get change points
	segment_type, change_points = [], []
	i = n
	while i > 1:
		for j in range(1, i - min_segment_len+1 + 1):
			if segment_is_degenerate(j, i): continue 
			if np.isclose(dp[i], dp[j-1] + segment_cost(j, i)[0] + penalization_linear(n)):
				segment_type.append((segment_cost(j, i)[1], j, i))
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				break
	if (len(change_points) > 0) and change_points[-1] > 1: segment_type.append((segment_cost(1, change_points[-1]-1)[1], 1, change_points[-1]-1))
	
	write_change_points(change_points, segment_type, ts_compressed, out_file_path)

	dt_cp = []
	for cp in change_points: dt_cp.append(ts_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path + ".png", ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp)

def create_dirs(server):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/" + server) == False: os.makedirs("./plots/" + server)

def has_enough_data(file_path):
	cnt = 0
	df = pd.read_csv(file_path)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		if dt <= dt_end and dt >= dt_start:
			cnt += 1
	
	max_number_of_measures = 48*(dt_end - dt_start).days
	if(float(cnt)/max_number_of_measures >= min_fraction_of_measures): return True
	return False


def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	
	server = "BGEDTCSRV04"
	mac = "64:66:B3:7B:91:24"
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./test"
	#segment_neighbourhood_linear_penalization(in_file_path, out_file_path)
	segment_neighbourhood(in_file_path, out_file_path)
	return
	
	in_dir = "../input/" + date_dir + "/"
	for server in os.listdir(in_dir):
		create_dirs(server)
		for file_name in os.listdir(in_dir + "/" + server):
			mac = file_name.split(".")[0]
			in_file_path = in_dir + "/" + server + "/" + file_name
			out_file_path = "./plots/" + server + "/" + mac
			
			if has_enough_data(in_file_path): segment_neighbourhood(in_file_path, out_file_path)
		
process()
