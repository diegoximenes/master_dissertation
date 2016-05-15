import os, math, sys
import pandas as pd
import numpy as np

import cProfile
import bayesian_changepoint_detection.offline_changepoint_detection as offcd
from functools import partial

sys.path.append("../../import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

#PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def get_change_points(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_compressed_ma = time_series.ma_smoothing(ts_compressed)	
	
	data = np.asarray(ts_compressed.y)
	if len(data) == 0: return

	q, p, pcp = offcd.offline_changepoint_detection(data, partial(offcd.const_prior, l = len(data) + 1), offcd.gaussian_obs_log_likelihood, truncate = -40)
	
	prob_list = np.exp(pcp).sum(0)
	
	#print "len(prob_list)=" + str(len(prob_list))
	#print "len(ts_compressed.x)=" + str(len(ts_compressed.x))

	ts_dist = time_series.dist_ts(ts_compressed)
	for i in xrange(len(ts_compressed.x)-1):
		ts_dist.x.append(ts_compressed.x[i])
		ts_dist.y.append(prob_list[i])
		ts_dist.dt_mean[ts_compressed.x[i]] = prob_list[i]
		
	plot_procedures.plot_ts_and_dist(ts, ts_dist, out_file_path + ".png", ylabel = metric, dist_ylabel = "p", dist_ylim = [-0.01, 1.01])

def create_dirs(server):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/bayesian_offline/") == False: os.makedirs("./plots/bayesian_offline/")
	if os.path.exists("./plots/bayesian_offline/" + date_dir) == False: os.makedirs("./plots/bayesian_offline/" + date_dir)
	if os.path.exists("./plots/bayesian_offline/" + date_dir + "/" + server) == False: os.makedirs("./plots/bayesian_offline/" + date_dir + "/" + server)

def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	create_dirs(server)
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./plots/bayesian_offline/" + date_dir + "/" + server + "/" + mac
	get_change_points(in_file_path, out_file_path)	
	return
		
	for server in os.listdir("../input/" + date_dir + "/"):
			print server
			create_dirs(server)
			for file_name in os.listdir("../input/" + date_dir + "/" + server + "/"):
				mac = file_name.split(".")[0]
				print mac
					
				in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
				out_file_path = "./plots/bayesian_offline/" + date_dir + "/" + server + "/" + mac
							
				get_change_points(in_file_path, out_file_path)	
	
process()
