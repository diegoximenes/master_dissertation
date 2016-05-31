import os, sys, datetime

sys.path.append("./import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

dt_start = datetime.datetime(2016, 5, 11)
number_of_days = 10
metric = "loss"

dt_end = dt_start + datetime.timedelta(days = number_of_days - 1) 
target_year, target_month = dt_start.year, dt_start.month
date_dir = str(target_year) + "_" + str(target_month).zfill(2)

in_dir = "./change_point_detection/input/" + date_dir

def create_dirs():
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end)) == False: os.makedirs("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end))
	if os.path.exists("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/filtered/") == False: os.makedirs("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/filtered/")
	if os.path.exists("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/not_filtered/") == False: os.makedirs("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/not_filtered/")

def filter_ts(ts):
	min_fraction_of_measures = 0.85
	window_len = 48
	threshold = 0.01
	min_number_of_measures_greater_than_threshold_inside_window = 6

	if float(len(ts.raw_x))/(24*2*number_of_days) < min_fraction_of_measures: return False

	for i in range(window_len-1, len(ts.raw_y)):
		cnt_greater_than_threshold = 0
		for j in range(i-window_len+1, i):
			if ts.raw_y[j] > threshold: 
				cnt_greater_than_threshold += 1
		if cnt_greater_than_threshold >= min_number_of_measures_greater_than_threshold_inside_window: return True

	return False

def process():
	create_dirs()
	for server in os.listdir(in_dir):
		print server
		for file_name in os.listdir(in_dir + "/" + server + "/"):
			mac = file_name.split(".")[0]
			
			in_file_path = in_dir + "/" + server + "/"+ file_name
			out_file_path_filtered =  "./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/filtered/" + server + "_" + mac + ".png"
			out_file_path_not_filtered =  "./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/not_filtered/" + server + "_" + mac + ".png"
			
			ts = TimeSeries(in_file_path, target_month, target_year, metric, dt_start, dt_end)
			if filter_ts(ts): out_file_path = out_file_path_filtered
			else: out_file_path = out_file_path_not_filtered
			plot_procedures.plot_ts(ts, out_file_path, ylim = [-0.02, 1.02], compressed = False)
				
process()
