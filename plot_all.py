import os, sys, datetime

sys.path.append("./import_scripts/")
import plot_procedures, time_series
from time_series import TimeSeries

dt_start, dt_end = datetime.datetime(2016, 5, 1), datetime.datetime(2016, 5, 7)
metric = "loss"

target_year, target_month = dt_start.year, dt_start.month
date_dir = str(target_year) + "_" + str(target_month).zfill(2)

in_dir = "./change_point_detection/input/" + date_dir

def create_dirs():
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end)) == False: os.makedirs("./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end))

def process():
	create_dirs()
	for server in os.listdir(in_dir):
		for file_name in os.listdir(in_dir + "/" + server + "/"):
			mac = file_name.split(".")[0]
			
			in_file_path = in_dir + "/" + server + "/"+ file_name
			out_file_path =  "./plots/dtstart" + str(dt_start) + "_dtend" + str(dt_end) + "/" + server + "_" + mac + ".png"
			
			ts = TimeSeries(in_file_path, target_month, target_year, metric, dt_start, dt_end)
			if float(len(ts.raw_x))/(24*2*7) >= 0.85: plot_procedures.plot_ts(ts, out_file_path, ylim = [-0.02, 1.02], compressed = True)
				
process()
