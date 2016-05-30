import os, ast, sys, datetime, calendar
import pandas as pd

import datetime_procedures

"""
- description:
	- returns a dic in which the keys are each hour of the target month and the value is the mean of the specified hour
- arguments
- returns:
	- dic:
		- key: datetime
		- value: mean of measures in strdt bin
"""
def get_dt_mean(in_file_path, metric, dt_start, dt_end):
	dt_list = datetime_procedures.generate_dt_list(dt_start, dt_end)
		
	dt_cntSum = {}
	for dt in dt_list: dt_cntSum[dt] = [0, 0]
	
	df = pd.read_csv(in_file_path)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		dt_rounded = datetime.datetime(dt.year, dt.month, dt.day, dt.hour)
		if dt_rounded not in dt_cntSum: continue

		dt_cntSum[dt_rounded][0] += 1
		dt_cntSum[dt_rounded][1] += row[metric]
	
	dt_mean = {}
	for dt in dt_cntSum:
		if dt_cntSum[dt][0] > 0: dt_mean[dt] = float(dt_cntSum[dt][1])/dt_cntSum[dt][0]
		else: dt_mean[dt] = None

	return dt_mean

"""
- description: 
- arguments
- returns:
	- raw_x: sorted datetimes
	- raw_y: values, according with raw_x
"""
def get_raw_data(in_file_path, metric, dt_start, dt_end):
	l = []
	df = pd.read_csv(in_file_path)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		if datetime_procedures.in_dt_range(dt, dt_start, dt_end): l.append([dt, row[metric]])
	raw_x, raw_y = [], []
	l.sort()
	for p in l:
		raw_x.append(p[0])
		raw_y.append(p[1])
	return raw_x, raw_y
