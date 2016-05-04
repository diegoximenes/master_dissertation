import os, math, sys
import numpy as np

sys.path.append("../../import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

#PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
max_segments = 10
penalization_type = "aic"
#penalization_type = "sic"
#penalization_type = "hannan_quinn"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def penalization(n, k):
	if penalization_type == "aic": return 2*k
	elif penalization_type == "sic": return np.log(n)*k
	elif penalization_type == "hannan_quinn": return np.log(np.log(n))*k

def get_prefix_sum(data):
	n = len(data)
	prefix_sum = np.zeros(n+1)
	prefix_sum[0] = 0
	for i in xrange(1, n+1): prefix_sum[i] = prefix_sum[i-1] + data[i-1]
	return prefix_sum

def get_mse_matrix(data):
	n = len(data)
	mse_mat = np.zeros(shape = (n+1, n+1))
	prefix_sum = get_prefix_sum(data)
	
	for i in xrange(1, n+1):
		mse_mat[i][i] = 0
		for j in xrange(i+1, n+1):
			last_mean = np.float(prefix_sum[j-1] - prefix_sum[i-1])/(j-1 - i + 1)
			mse_mat[i][j] = mse_mat[i][j-1] + np.float(j-i)/(j-i+1)*(data[j-1] - last_mean)**2
	
	return mse_mat 

def segment_neighbourhood(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	n = len(ts_ma_compressed.y)
	mse_mat = get_mse_matrix(ts_ma_compressed.y)

	#calculate dp
	dp = np.zeros(shape = (max_segments+1, n+1))	
	for i in xrange(1, n+1): dp[0][i] = float("inf")
	for n_segments in xrange(1, max_segments+1):
		for i in xrange(1, n+1):
			dp[n_segments][i] = float("inf")
			for j in xrange(1, i+1): 
				dp[n_segments][i] = min(dp[n_segments][i], dp[n_segments-1][j-1] + mse_mat[j][i])
	
	#get best number of segments
	best_n_segments = 1
	for n_segments in xrange(2, max_segments+1):
		if dp[n_segments][n] + penalization(n, n_segments) <= dp[best_n_segments][n] + penalization(n, best_n_segments):
			best_n_segments = n_segments

	#backtrack: get change points
	change_points = []
	i, n_segments = n, best_n_segments
	while n_segments > 1:
		for j in range(1, i+1):
			if np.isclose(dp[n_segments][i], dp[n_segments-1][j-1] + mse_mat[j][i]):
				change_points.append(j) #CHECK THIS INDEX
				i = j-1
				n_segments -= 1
				break
	
	strdt_cp = []
	for cp in change_points: strdt_cp.append(ts_compressed.x[cp-1])
	plot_procedures.plot_ts(ts_ma, out_file_path, ylabel = "loss", ylim = [-0.01, 1.01], strdt_axvline = strdt_cp)
		
def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./test.png"
	segment_neighbourhood(in_file_path, out_file_path)

process()
