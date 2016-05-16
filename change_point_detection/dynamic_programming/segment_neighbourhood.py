import os, math, sys
import numpy as np

sys.path.append("../../import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

#PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
max_segments = 10 #not used in O(n**2) solution
min_segment_len = 1
#cost_type = "mse"
#cost_type = "likelihood_normal"
cost_type = "likelihood_exponential"
#cost_type = "likelihood_all" #consider that all likelihood distributions can be used
#penalization_type = "aic"
penalization_type = "sic"
#penalization_type = "hannan_quinn"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def penalization(n, k):
	if penalization_type == "aic": return 2*k
	elif penalization_type == "sic": return 2*np.log(n)*k
	elif penalization_type == "hannan_quinn": return np.log(np.log(n))*k
def penalization_linear(n):
	if penalization_type == "aic": return 2
	elif penalization_type == "sic": return 2*np.log(n)
	elif penalization_type == "hannan_quinn": return 2*np.log(np.log(n))

def get_mean(i, j):
	return np.float(prefix_sum[j] - prefix_sum[i-1])/(j-i+1)

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
			squared_std = mse_mat[i][j]
			if np.isclose(squared_std, 0): normal_log_likelihood_mat[i][j] = np.log(1)
			else: normal_log_likelihood_mat[i][j] = -0.5*(j-i+1)*np.log(2*np.pi*squared_std) - 0.5*(j-i+1)

def calc_exponential_log_likelihood_matrix(data):
	global exponential_log_likelihood_mat 
	n = len(data)
	exponential_log_likelihood_mat = np.zeros(shape = (n+1, n+1))
	for i in xrange(1, n+1):
		for j in xrange(i+1, n+1):
			lmbd = np.float(j-i+1)/(prefix_sum[j] - prefix_sum[i-1])
			exponential_log_likelihood_mat[i][j] = (j-i+1)*np.log(lmbd) - lmbd*(prefix_sum[j] - prefix_sum[i-1])
			
def segment_cost(i, j):
	if cost_type == "mse": return (2*mse_mat[i][j], "mse")
	elif cost_type == "likelihood_normal": return (-2*normal_log_likelihood_mat[i][j], "likelihood_normal")
	elif cost_type == "likelihood_exponential": return (-2*exponential_log_likelihood_mat[i][j], "likelihood_exponential")
	elif cost_type == "likelihood_all": 	
		normal_cost = -2*normal_log_likelihood_mat[i][j]
		exponential_cost = -2*exponential_log_likelihood_mat[i][j]
		if normal_cost <= exponential_cost: return (normal_cost, "likelihood_normal")
		else: return (exponential_cost, "likelihood_exponential")

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
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	
	n = len(ts_compressed.y)
	calc_prefix_sum(ts_compressed.y)
	calc_mse_matrix(ts_compressed.y)
	calc_exponential_log_likelihood_matrix(ts_compressed.y)
	if cost_type == "likelihood_all" or cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_compressed.y)

	#calculate dp
	dp = np.zeros(shape = (max_segments+1, n+1))	
	for i in xrange(1, n+1): dp[0][i] = float("inf")
	for n_segments in xrange(1, max_segments+1):
		print n_segments
		for i in xrange(1, n+1):
			dp[n_segments][i] = float("inf")
			for j in xrange(1, i - min_segment_len+1 + 1): 
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
			if np.isclose(dp[n_segments][i], dp[n_segments-1][j-1] + segment_cost(j, i)[0]):
				segment_type.append((segment_cost(j, i)[1], j, i))
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				n_segments -= 1
				break
	if change_points[-1] > 1: segment_type.append((segment_cost(1, change_points[-1]-1)[1], 1, change_points[-1]-1))
	
	write_change_points(change_points, segment_type, ts_compressed, out_file_path)
			
	dt_cp = []
	for cp in change_points: dt_cp.append(ts_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path + ".png", ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp)

"""
can only be used on penalization(n, k) = f(n)*k
"""
def segment_neighbourhood_linear_penalization(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	
	n = len(ts_compressed.y)
	calc_prefix_sum(ts_compressed.y)
	calc_mse_matrix(ts_compressed.y)
	calc_exponential_log_likelihood_matrix(ts_compressed.y)
	if cost_type == "likelihood_all" or cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_compressed.y)

	#calculate dp
	dp = np.zeros(n+1)	
	for i in xrange(1, n+1): dp[i] = float("inf")
	for i in xrange(1, n+1):
		dp[i] = float("inf")
		for j in xrange(1, i - min_segment_len+1 + 1): 
			dp[i] = min(dp[i], dp[j-1] + segment_cost(j, i)[0] + penalization_linear(n))
	
	#backtrack: get change points
	segment_type, change_points = [], []
	i = n
	while i > 1:
		for j in range(1, i - min_segment_len + 1):
			if np.isclose(dp[i], dp[j-1] + segment_cost(j, i)[0] + penalization_linear(n)):
				segment_type.append((segment_cost(j, i)[1], j, i))
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				break
	if change_points[-1] > 1: segment_type.append((segment_cost(1, change_points[-1]-1)[1], 1, change_points[-1]-1))
	
	write_change_points(change_points, segment_type, ts_compressed, out_file_path)

	dt_cp = []
	for cp in change_points: dt_cp.append(ts_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path + ".png", ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp)

def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./test"
	segment_neighbourhood_linear_penalization(in_file_path, out_file_path)
	#segment_neighbourhood(in_file_path, out_file_path)

process()
