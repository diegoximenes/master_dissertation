import sys, datetime, os
import pandas as pd
from random import shuffle

sys.path.append("../../../import_scripts/")
import datetime_procedures, time_series
from time_series import TimeSeries

#parameters
dt_start1 = datetime.datetime(2016, 5, 1)
dt_start2 = datetime.datetime(2016, 5, 11)
number_of_days = 10
metric = "loss"

dt_end1 = dt_start1 + datetime.timedelta(days = number_of_days - 1) 
dt_end2 = dt_start2 + datetime.timedelta(days = number_of_days - 1) 
target_year1, target_month1 = dt_start1.year, dt_start1.month
target_year2, target_month2 = dt_start2.year, dt_start2.month
date_dir1 = str(target_year1) + "_" + str(target_month1).zfill(2)
date_dir2 = str(target_year2) + "_" + str(target_month2).zfill(2)
in_dir1 = "../../input/" + date_dir1
in_dir2 = "../../input/" + date_dir2

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

def get_filtered_ts(dt_start, dt_end, in_dir, target_month, target_year):
	filtered_ts_list = []

	date_start = str(target_month).zfill(2) + "/" + str(dt_start.day).zfill(2) + "/" + str(target_year)
	date_end = str(target_month).zfill(2) + "/" + str(dt_end.day).zfill(2) + "/" + str(target_year)

	for server in os.listdir(in_dir):
		print server
		for file_name in os.listdir(in_dir + "/" + server + "/"): 
			mac = file_name.split(".")[0]
			csv_path = in_dir + "/" + server + "/" + file_name
			
			ts = TimeSeries(csv_path, target_month, target_year, metric, dt_start, dt_end)
			if filter_ts(ts): filtered_ts_list.append([mac, server, csv_path, date_start, date_end])
	return filtered_ts_list

def write_to_file(l):
	file = open("ts_to_be_inserted.csv", "w")
	file.write("mac,server,csv_path,date_start,date_end\n")
	for p in l: file.write(str(p[0]) + "," + str(p[1]) + "," + str(p[2]) + "," + str(p[3]) + "," + str(p[4]) + "\n")
	file.close()

filtered_ts_list = get_filtered_ts(dt_start1, dt_end1, in_dir1, target_month1, target_year1) 
filtered_ts_list += get_filtered_ts(dt_start2, dt_end2, in_dir2, target_month2, target_year2) 
shuffle(filtered_ts_list)

write_to_file(filtered_ts_list)
