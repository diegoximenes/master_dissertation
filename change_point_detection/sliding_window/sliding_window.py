import os, math, sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt

sys.path.append("/home/diegoximenes/Documents/data_analysis/import_scripts/")
import plot, time_series
from time_series import TimeSeries

target_year, target_month = 2015, 12

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def create_dirs(server):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/sliding_window/") == False: os.makedirs("./plots/sliding_window/")
	if os.path.exists("./plots/sliding_window/" + date_dir) == False: os.makedirs("./plots/sliding_window/" + date_dir)
	if os.path.exists("./plots/sliding_window/" + date_dir + "/" + server) == False: os.makedirs("./plots/sliding_window/" + date_dir + "/" + server)

def bhattacharyya_coef(distr1, distr2):
	sum1, sum2, coef = np.sum(distr1), np.sum(distr2), 0
	
	#no distribution
	if (sum1 == 0) or (sum2 == 0): return -1
	
	for i in range(len(distr1)): coef += math.sqrt(float(distr1[i])/float(sum1) * float(distr2[i])/float(sum2))
	
	return coef

def bhattacharyya_dist(distr1, distr2):
	bhat_coef = bhattacharyya_coef(distr1, distr2)
	if bhat_coef < 0: return -1
	#FIX THIS
	if bhat_coef == 0: return 1
	return -math.log(bhat_coef)

def hellinger_dist(distr1, distr2):
	bhat_coef = bhattacharyya_coef(distr1, distr2)
	if bhat_coef < 0: return -1
	return math.sqrt(1 - bhat_coef)

def get_distr(l, metric):
	if metric == "loss": delta, min_bin, max_bin = 0.01, 0.01, 1
	
	bins = np.arange(min_bin, max_bin + delta, delta)
	distr = [0]*len(bins)

	for x in l:
		bin = 0
		while bin < len(bins):
			if x <= bins[bin]: break
			bin += 1
		distr[bin] += 1	

	return np.asarray(distr)/float(np.sum(distr))

def mean_dist(l1, l2):
	return abs(np.mean(l1) - np.mean(l2))

def distance(l1, l2, metric):
	distr1 = get_distr(l1, metric)	
	distr2 = get_distr(l2, metric)	
	return mean_dist(l1, l2)
	#return hellinger_dist(distr1, distr2)
	#return bhattacharyya_dist(distr1, distr2)

def plot_ts_and_dist(ts, ts_dist, out_file_path, ylabel):
	min_len = 100
	if len(ts.y) < min_len or len(ts_dist.y) < min_len:
		print "less points than necessary"
		return
	
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	f, ax = plt.subplots(2, 1, figsize = (16, 12), sharex = "col")
		
	strdt_bin = {}
	for strdt in sorted(list(ts.strdt_mean.keys())): strdt_bin[strdt] = len(strdt_bin)

	xticks, xticks_labels = plot.get_xticks(strdt_bin)

	x, y = [], []
	for i in range(len(ts.y)): 
		if ts.y[i] != None:
			x.append(strdt_bin[ts.x[i]])
			y.append(ts.y[i])
	
	x_dist, y_dist = [], []
	for i in range(len(ts_dist.y)): 
		if ts_dist.y[i] != None:
			x_dist.append(strdt_bin[ts_dist.x[i]])
			y_dist.append(ts_dist.y[i])
	
	ax[0].grid()
	ax[0].set_ylabel(ylabel)
	ax[0].set_xticks(xticks)
	ax[0].set_xlim([min(xticks), max(xticks) + 24])
	ax[0].scatter(x, y, s = 10)
	
	ax[1].grid()
	ax[1].set_ylabel("bhat dist")
	ax[1].set_xticks(xticks)
	ax[1].set_xticklabels(xticks_labels, rotation = "vertical")
	ax[0].set_xlim([min(xticks), max(xticks) + 24])
	ax[1].plot(x_dist, y_dist)
	
	plt.savefig(out_file_path + ".png")
	plt.close("all")

def sliding_window(in_file_path, out_file_path, metric):
	window_len = 24
	
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)

	ts_dist = TimeSeries()
	for i in range(window_len, len(ts_compressed.y) - window_len + 1):
		strdt = ts_compressed.x[i]
		dist = distance(ts_compressed.y[i - window_len : i], ts_compressed.y[i : i + window_len], "loss")

		ts_dist.strdt_mean[strdt] = dist
		ts_dist.x.append(strdt)
		ts_dist.y.append(dist)
	
	plot_ts_and_dist(ts, ts_dist, out_file_path, metric)
		
def get_change_points():
	cnt = 0
	
	"""	
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	sliding_window("./input/" + date_dir + "/" + server + "/" + mac + ".csv", "./test.png", "loss")
	return
	"""
		
	for server in os.listdir("./input/" + date_dir + "/"):
		print server
		create_dirs(server)
		for file_name in os.listdir("./input/" + date_dir + "/" + server + "/"):
			mac = file_name.split(".")[0]
			cnt += 1
			print "cnt=" + str(cnt)
			
			in_file_path = "./input/" + date_dir + "/" + server + "/" + mac + ".csv"
			out_file_path = "./plots/sliding_window/" + date_dir + "/" + server + "/" + mac

			dist_list = sliding_window(in_file_path, out_file_path, "loss")
			
get_change_points()
