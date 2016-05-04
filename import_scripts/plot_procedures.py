import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.append("../general_scripts/")
import datetime_procedures

def get_xticks(strdt_bin):
	xticks, xticks_labels = [], [] 
	for strdt in strdt_bin:
		if "00:00:00" in strdt.split(" ")[-1]:
			dt = datetime_procedures.from_strDatetime_to_datetime(strdt)
			xticks.append(strdt_bin[strdt])
			xticks_labels.append(str(dt.day).zfill(2) + "/" + str(dt.month).zfill(2))
	return xticks, xticks_labels

def plot_ts_and_dist(ts, ts_dist, out_file_path, ylabel, dist_ylabel = "", dist_ylim = None):
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	f, ax = plt.subplots(2, 1, figsize = (16, 12), sharex = "col")
		
	strdt_bin = {}
	for strdt in sorted(list(ts.strdt_mean.keys())): strdt_bin[strdt] = len(strdt_bin)

	xticks, xticks_labels = get_xticks(strdt_bin)

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
	ax[0].set_ylim([-0.01, 1.01])
	ax[0].scatter(x, y, s = 10)
	
	ax[1].grid()
	ax[1].set_ylabel(dist_ylabel)
	ax[1].set_xticks(xticks)
	ax[1].set_xticklabels(xticks_labels, rotation = "vertical")
	ax[0].set_xlim([min(xticks), max(xticks) + 24])
	if dist_ylim != None: ax[1].set_ylim(dist_ylim)
	ax[1].plot(x_dist, y_dist)
	
	plt.savefig(out_file_path)
	plt.close("all")

def plotax_ts(ax, ts, strdt_axvline = {}, ylabel = "", ylim = None):
	strdt_bin = {}
	for strdt in sorted(list(ts.strdt_mean.keys())): strdt_bin[strdt] = len(strdt_bin)

	x, y = [], []	
	for i in range(len(ts.y)):
		if ts.y[i] != None:
			x.append(strdt_bin[ts.x[i]])
			y.append(ts.y[i])
	
	xticks, xticks_labels = get_xticks(strdt_bin)
		
	for strdt in strdt_axvline: 
		ax.axvline(strdt_bin[strdt], color = "r", linewidth = 1.0)

	ax.grid()
	ax.set_xticks(xticks)
	ax.set_xticklabels(xticks_labels, rotation = "vertical")
	ax.set_xlim([min(xticks), max(xticks) + 24])
	if ylim != None: ax.set_ylim(ylim)
	ax.set_ylabel(ylabel)
	ax.scatter(x, y, s = 10)

def plot_ts(ts, out_file_path, dt_axvline = {}, ylabel = "", ylim = None, strdt_axvline = []):
	strdt_bin = {}
	for strdt in sorted(list(ts.strdt_mean.keys())): strdt_bin[strdt] = len(strdt_bin)

	x, y = [], []	
	for i in range(len(ts.y)):
		if ts.y[i] != None:
			x.append(strdt_bin[ts.x[i]])
			y.append(ts.y[i])
	
	xticks, xticks_labels = get_xticks(strdt_bin)
		
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	plt.gcf().set_size_inches(15, 12)		
	
	for dt in dt_axvline: 
		strdt = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2) + " " + str(dt.hour).zfill(2) + ":00:00"
		plt.axvline(strdt_bin[strdt], color = "r", linewidth = 2.0)
	
	for strdt in strdt_axvline: plt.axvline(strdt_bin[strdt], color = "r", linewidth = 2.0)

	plt.grid()
	plt.xticks(xticks, xticks_labels, rotation = "vertical")
	plt.xlim([min(xticks), max(xticks) + 24])
	if ylim != None: plt.ylim(ylim)
	plt.ylabel(ylabel)
	plt.scatter(x, y, s = 10)
	plt.savefig(out_file_path)
	plt.close("all")

############################################################################################
############################################################################################
#LEGACY CODE
############################################################################################
############################################################################################

y_lim = {}
y_lim["loss"] = [-0.05, 1.01]

def get_data_plot(datetime_measure, datetime_bin):
	x, y = [], []
	for datetime in datetime_measure:
		x.append(datetime_bin[datetime])
		y.append(datetime_measure[datetime])
	return x, y

def plot_month_time_series(mac, metric, x, y, date, out_file_path, vline_x = None, ylim = None, log = False, symlog = False):
	datetime_bin = datetime_procedures.generate_bins_month(date)
	xticks, xticks_labels = datetime_procedures.get_xticks_bins_month(date, datetime_bin)

	plt.clf()
	fig = plt.figure()
	fig.set_size_inches(22, 13)
	ax = fig.gca()
	plt.scatter(x, y, s = 8)
	if ylim != None: ax.set_ylim(ylim)
	elif metric in y_lim: ax.set_ylim(y_lim[metric])
	ax.set_xticks(xticks)
	ax.set_xticklabels(xticks_labels, rotation = 90, fontsize = 12)
	ax.set_ylabel(metric)
	ax.set_xlabel("day")
	
	if vline_x != None: plt.axvline(vline_x, color = "r")	
	if log == True: ax.set_yscale("log")
	if symlog == True: ax.set_yscale("symlog", linthreshy = 1e-4)

	plt.savefig(out_file_path, dpi = 96)
	plt.close("all")

def plot_ts_from_file(metric, in_file, out_file, datetimes_axvline, ma_smoothing, target_month, target_year):
	ma_smoothing_window_len = 5

	strdt_bin = datetime_procedures.generate_hourly_bins_month([target_month, target_year])
	
	strdt_cntSum = {}
	for strdt in strdt_bin: strdt_cntSum[strdt] = [0, 0]
	
	df = pd.read_csv(in_file)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		strdt = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2) + " " + str(dt.hour).zfill(2) + ":00:00"
		
		if strdt not in strdt_cntSum: continue
		
		strdt_cntSum[strdt][0] += 1
		strdt_cntSum[strdt][1] += row[metric]

	strdt_list = []
	for strdt in strdt_bin: strdt_list.append(strdt)
	strdt_list.sort()
	x, y = [], []
	xticks, xticks_labels = datetime_procedures.get_xticks_bins_month([target_month, target_year], strdt_bin)
	if ma_smoothing == False:
		for strdt in strdt_list:
			if strdt_cntSum[strdt][0] > 0:
				mean = float(strdt_cntSum[strdt][1])/strdt_cntSum[strdt][0]
				x.append(strdt_bin[strdt])
				y.append(mean)
	else:		
		for i in xrange(len(strdt_list)):
			ysum, ycnt = 0, 0
			for j in range(max(0, i - ma_smoothing_window_len), min(len(strdt_list)-1, i + ma_smoothing_window_len) + 1):
				if strdt_cntSum[strdt_list[j]][0] > 0: 
					ysum += float(strdt_cntSum[strdt_list[j]][1])/strdt_cntSum[strdt_list[j]][0]
					ycnt += 1
			if ycnt > 0:
				x.append(strdt_bin[strdt_list[i]])
				y.append(ysum/ycnt)
	
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	plt.gcf().set_size_inches(15, 12)		
	
	if datetimes_axvline != None:
		for dt in datetimes_axvline: 
			strdt = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2) + " " + str(dt.hour).zfill(2) + ":00:00"
			plt.axvline(strdt_bin[strdt], color = "r", linewidth = 2.0)

	plt.scatter(x, y, s = 10)
	plt.grid()
	plt.ylabel(metric)
	plt.xticks(xticks, xticks_labels, rotation = "vertical")
	plt.savefig(out_file)
	plt.close("all")
