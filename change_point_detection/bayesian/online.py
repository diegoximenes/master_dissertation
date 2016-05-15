import os, math, sys
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.pylab as plt

import cProfile
import bayesian_changepoint_detection.online_changepoint_detection as oncd
from functools import partial

sys.path.append("../../import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

#PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
number_of_future_samples_to_consider = 10

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def get_change_points(in_file_path, out_file_path):
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	data = np.asarray(ts_compressed.y)
	if len(data) == 0: return

	prob_length, map_estimates = oncd.online_changepoint_detection(data, partial(oncd.constant_hazard, 250), oncd.StudentT(0.1, .01, 1, 0))
		
	prob_list = prob_length[number_of_future_samples_to_consider, number_of_future_samples_to_consider:-1]
	
	fig, ax = plt.subplots(figsize=[18, 16])
	ax = fig.add_subplot(3, 1, 1)
	ax.scatter(range(len(ts_compressed.y)), ts_compressed.y)
	ax = fig.add_subplot(3, 1, 2, sharex=ax)
	sparsity = 5  # only plot every fifth data for faster display
	ax.pcolor(np.array(range(0, len(prob_length[:,0]), sparsity)), np.array(range(0, len(prob_length[:,0]), sparsity)), -np.log(prob_length[0:-1:sparsity, 0:-1:sparsity]), cmap=cm.Greys, vmin=0, vmax=30)
	ax = fig.add_subplot(3, 1, 3, sharex=ax)
	ax.plot(prob_length[number_of_future_samples_to_consider,number_of_future_samples_to_consider:-1])
	plt.show()	
	return	

	ts_dist = TimeSeries()
	for i in xrange(len(prob_list)-1):
		ts_dist.x.append(ts_compressed.x[i])
		ts_dist.y.append(prob_list[i])
		ts_dist.dt_mean[ts_compressed.x[i]] = prob_list[i]
		
	plot_procedures.plot_ts_and_dist(ts, ts_dist, out_file_path + ".png", ylabel = metric, dist_ylabel = "p", dist_ylim = [-0.01, 1.01])

def create_dirs(server):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/bayesian_online/") == False: os.makedirs("./plots/bayesian_online/")
	if os.path.exists("./plots/bayesian_online/" + date_dir) == False: os.makedirs("./plots/bayesian_online/" + date_dir)
	if os.path.exists("./plots/bayesian_online/" + date_dir + "/" + server) == False: os.makedirs("./plots/bayesian_online/" + date_dir + "/" + server)

def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	create_dirs(server)
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./plots/bayesian_online/" + date_dir + "/" + server + "/" + mac
	get_change_points(in_file_path, out_file_path)	
	return

	for server in os.listdir("../input/" + date_dir + "/"):
			print server
			create_dirs(server)
			for file_name in os.listdir("../input/" + date_dir + "/" + server + "/"):
				mac = file_name.split(".")[0]
				print mac
					
				in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
				out_file_path = "./plots/bayesian_online/" + date_dir + "/" + server + "/" + mac
							
				get_change_points(in_file_path, out_file_path)	
	
process()
