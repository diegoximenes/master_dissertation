import sys, datetime
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import datetime_procedures

#daily xticks
def get_xticks(dt_start, dt_end):
	xticks, xticks_labels = [], []
	for i in range((dt_end - dt_start).days + 2):
		dt = dt_start + datetime.timedelta(days = i)
		xticks.append(dt)
		xticks_labels.append(str(dt.day).zfill(2) + "/" + str(dt.month).zfill(2))
	return xticks, xticks_labels

def plot_ts(ts, out_file_path, plot_raw_data = True, dt_axvline = [], ylabel = "", ylim = None):
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	plt.gcf().set_size_inches(15, 12)		
		
	xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)	
	
	for dt in dt_axvline: plt.axvline(dt, color = "r", linewidth = 2.0)

	plt.grid()
	if ylim != None: plt.ylim(ylim)
	plt.ylabel(ylabel)
	plt.xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days = 1)])
	plt.xticks(xticks, xticks_labels, rotation = "vertical")
	if plot_raw_data: plt.scatter(ts.raw_x, ts.raw_y, s = 9)
	else: plt.scatter(ts.x, ts.y, s = 9)
	plt.savefig(out_file_path)
	plt.close("all")

def plot_ts_and_dist(ts, ts_dist, out_file_path, plot_raw_data = True, ylabel = "", dist_ylabel = "", ylim = None, dist_ylim = None, dist_plot_type = "plot", dist_yticks = None, dist_yticklabels = None):
	plt.clf()
	matplotlib.rcParams.update({'font.size': 13})
	f, ax = plt.subplots(2, 1, figsize = (16, 12), sharex = "col")
		
	xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)

	ax[0].grid()
	ax[0].set_ylabel(ylabel)
	ax[0].set_xticks(xticks)
	ax[0].set_xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days = 1)])
	ax[0].set_yticks(np.arange(0, 1 + 0.05, 0.05))
	ax[0].set_ylim([-0.02, 1.02])
	if plot_raw_data: ax[0].scatter(ts.raw_x, ts.raw_y, s = 9)
	else: plt.scatter(ts.x, ts.y, s = 9)
	
	ax[1].grid()
	ax[1].set_ylabel(dist_ylabel)
	ax[1].set_xticks(xticks)
	ax[1].set_xticklabels(xticks_labels, rotation = "vertical")
	ax[1].set_xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days = 1)])
	if dist_ylim != None: ax[1].set_ylim(dist_ylim)
	if dist_yticks != None: ax[1].set_yticks(dist_yticks)
	if dist_yticklabels != None: ax[1].set_yticklabels(dist_yticklabels)
	if dist_plot_type == "plot": ax[1].plot(ts_dist.x, ts_dist.y)
	elif dist_plot_type == "scatter": ax[1].scatter(ts_dist.x, ts_dist.y)
		
	plt.savefig(out_file_path)
	plt.close("all")

def plotax_ts(ax, ts, plot_raw_data = True, dt_axvline = [], ylabel = "", ylim = None):
	for dt in dt_axvline: plt.axvline(dt, color = "r", linewidth = 2.0)
	
	xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)	
	
	ax.grid()
	ax.set_xticks(xticks)
	ax.set_xticklabels(xticks_labels, rotation = "vertical")
	ax.set_xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days = 1)])
	if ylim != None: ax.set_ylim(ylim)
	ax.set_ylabel(ylabel)
	if plot_raw_data: ax.scatter(ts.raw_x, ts.raw_y, s = 9)
	else: ax.scatter(ts.x, ts.y, s = 9)
