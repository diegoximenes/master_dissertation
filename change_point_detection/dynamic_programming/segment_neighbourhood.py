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
	if cost_type == "mse": return 2*mse_mat[i][j]
	elif cost_type == "likelihood_normal": return -2*normal_log_likelihood_mat[i][j]
	elif cost_type == "likelihood_exponential": return -2*exponential_log_likelihood_mat[i][j]

def segment_neighbourhood(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	n = len(ts_ma_compressed.y)
	calc_prefix_sum(ts_ma_compressed.y)
	calc_mse_matrix(ts_ma_compressed.y)
	calc_exponential_log_likelihood_matrix(ts_ma_compressed.y)
	if cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_ma_compressed.y)

	#calculate dp
	dp = np.zeros(shape = (max_segments+1, n+1))	
	for i in xrange(1, n+1): dp[0][i] = float("inf")
	for n_segments in xrange(1, max_segments+1):
		print n_segments
		for i in xrange(1, n+1):
			dp[n_segments][i] = float("inf")
			for j in xrange(1, i - min_segment_len+1 + 1): 
				dp[n_segments][i] = min(dp[n_segments][i], dp[n_segments-1][j-1] + segment_cost(j, i))
	
	#get best number of segments
	best_n_segments = 1
	for n_segments in xrange(2, max_segments+1):
		if dp[n_segments][n] + penalization(n, n_segments) <= dp[best_n_segments][n] + penalization(n, best_n_segments):
			best_n_segments = n_segments

	#backtrack: get change points
	change_points = []
	i, n_segments = n, best_n_segments
	while n_segments > 1:
		for j in range(1, i - min_segment_len+1 + 1):
			if np.isclose(dp[n_segments][i], dp[n_segments-1][j-1] + segment_cost(j, i)):
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				n_segments -= 1
				break
	
	strdt_cp = []
	for cp in change_points: strdt_cp.append(ts_ma_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path, ylabel = "loss", ylim = [-0.01, 1.01], strdt_axvline = strdt_cp)

"""
can only be used on penalization(n, k) = f(n)*k
"""
def segment_neighbourhood_linear_penalization(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	n = len(ts_ma_compressed.y)
	calc_prefix_sum(ts_ma_compressed.y)
	calc_mse_matrix(ts_ma_compressed.y)
	calc_exponential_log_likelihood_matrix(ts_ma_compressed.y)
	if cost_type == "likelihood_normal": calc_normal_log_likelihood_matrix(ts_ma_compressed.y)

	#calculate dp
	dp = np.zeros(n+1)	
	for i in xrange(1, n+1): dp[i] = float("inf")
	for i in xrange(1, n+1):
		dp[i] = float("inf")
		for j in xrange(1, i - min_segment_len+1 + 1): 
			dp[i] = min(dp[i], dp[j-1] + segment_cost(j, i) + penalization_linear(n))
	
	#backtrack: get change points
	change_points = []
	i = n
	while i > 1:
		for j in range(1, i - min_segment_len + 1):
			if np.isclose(dp[i], dp[j-1] + segment_cost(j, i) + penalization_linear(n)):
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				break
	
	strdt_cp = []
	for cp in change_points: strdt_cp.append(ts_ma_compressed.x[cp-1])
	plot_procedures.plot_ts(ts, out_file_path, ylabel = "loss", ylim = [-0.01, 1.01], strdt_axvline = strdt_cp)

def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./test.png"
	segment_neighbourhood_linear_penalization(in_file_path, out_file_path)
	#segment_neighbourhood(in_file_path, out_file_path)

process()
