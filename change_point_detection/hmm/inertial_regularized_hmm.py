import sys, os
import numpy as np

#import inertial_regularized_hmm.GaussianHMM as inertial_hmm

sys.path.append("../../import_scripts/")
import time_series, plot_procedures
from time_series import TimeSeries

sys.path.append("./inertial_regularized_hmm")
import GaussianHMM as inertial_hmm

#PARAMETERS
target_month, target_year = 12, 2015
metric = "loss"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def process():
	mac = "64:66:B3:50:03:A2"
	server = "NHODTCSRV04"
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	out_file_path = "./test_inertialhmm.png"
	
	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	ts_compressed = time_series.get_compressed(ts)
	ts_ma = time_series.ma_smoothing(ts)
	ts_ma_compressed = time_series.get_compressed(ts_ma)
	
	number_of_states = 4
	
	data = np.asarray(ts_compressed.y).reshape((len(ts_compressed.y), 1))

	rgzn_modes = inertial_hmm.GaussianHMM.RgznModes()
	model = inertial_hmm.GaussianHMM(number_of_states, data, rgzn_modes.INERTIAL)
	model.learn(data, zeta = 0.8)
	hidden_state_path = model.decode(data)
	
	ts_dist = TimeSeries()
	for i in range(len(ts_compressed.x)):
		strdt = ts_compressed.x[i]
		ts_dist.strdt_mean[strdt] = hidden_state_path[i]
		ts_dist.x.append(strdt)
		ts_dist.y.append(hidden_state_path[i])
	
	plot_procedures.plot_ts_and_dist(ts, ts_dist, out_file_path, metric, dist_ylabel = "hidden states", plot_type = "scatter", dist_ylim = [0-0.5, number_of_states-1+0.5], dist_yticks = range(number_of_states))
		
process()
