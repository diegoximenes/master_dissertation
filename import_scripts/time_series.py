import sys, datetime, calendar
import pandas as pd

import datetime_procedures, read_input

"""
- description:
	- by now this class represents month univariate time series
- attributes:
	- dt_mean:
	- x: strdt
	- y: value
	- raw_x: sorted raw datetime
	- raw_y: value, according with raw_x
	- dt_start: datetime of the first day considered
	- dt_end: datetime of the last day considered
"""
class TimeSeries:
	def __init__(self, in_file_path = None, target_month = None, target_year = None, metric = None):
		self.dt_mean = {}
		self.x = []
		self.y = []
		self.raw_x = []
		self.raw_y = []
		self.dt_start = None
		self.dt_end = None

		if in_file_path != None: self.read(in_file_path, target_month, target_year, metric)
				
	def read(self, in_file_path, target_month, target_year, metric):
		self.dt_start = datetime.datetime(target_year, target_month, 1)
		self.dt_end = datetime.datetime(target_year, target_month, calendar.monthrange(target_year, target_month)[-1])

		self.dt_mean = read_input.get_dt_mean(in_file_path, target_month, target_year, metric, self.dt_start, self.dt_end)
		ts = from_dic_to_list_ts(self.dt_mean)
		self.x = ts[0]
		self.y = ts[1]
		self.raw_x, self.raw_y = read_input.get_raw_data(in_file_path, target_month, target_year, metric)

"""
- description:
	- return a TimeSeries with same dt_start, dt_end as the argument, but with other attributes empty 
- arguments:
- return:
"""
def dist_ts(ts):
	ts_ret = TimeSeries()
	ts_ret.dt_start = ts.dt_start
	ts_ret.dt_end = ts.dt_end
	return ts_ret

"""
- description:
	- apply smoothing moving average. Example: ts[t] = (ts[t-1] + ts[t] + ts[t+1])/3
- argument:
	- ts: must not be compressed
	- window_len: must be odd	
- returns:
	- TimeSeries not compressed
"""
def ma_smoothing(ts, window_len = 11):
	ts_ret = TimeSeries()
	ts_ret.dt_start = ts.dt_start
	ts_ret.dt_end = ts.dt_end
	ts_ret.raw_x = list(ts.raw_x)
	ts_ret.raw_y = list(ts.raw_y)

	for i in xrange(len(ts.y)):
		ysum, ycnt = 0, 0
		for j in range(max(0, i - window_len/2), min(len(ts.y) - 1, i + window_len/2) + 1):
			if ts.y[j] != None: 
				ysum += ts.y[j]
				ycnt += 1

		ts_ret.x.append(ts.x[i])
		
		if ycnt > 0: val = float(ysum)/ycnt
		else: val = None
		ts_ret.y.append(val)	
		ts_ret.dt_mean[ts.x[i]] = val

	return ts_ret

"""
- description:
	- remove None from time series
- arguments:
- returns:
	- TimeSeries compressed
"""
def get_compressed(ts):
	ts_ret = TimeSeries()
	ts_ret.dt_start = ts.dt_start
	ts_ret.dt_end = ts.dt_end
	ts_ret.raw_x = list(ts.raw_x)
	ts_ret.raw_y = list(ts.raw_y)

	for i in range(len(ts.y)):
		if ts.y[i] != None:
			ts_ret.x.append(ts.x[i])		
			ts_ret.y.append(ts.y[i])	
		ts_ret.dt_mean[ts.x[i]] = ts.y[i]
	return ts_ret

"""
- description:
- argument:
- returns: 
"""
def from_dic_to_list_ts(dt_measure):	
	x, y = [], []
	for dt in sorted(list(dt_measure.keys())):
		x.append(dt)
		y.append(dt_measure[dt])
	return [x, y]
