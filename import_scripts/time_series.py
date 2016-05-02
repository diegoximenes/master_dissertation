import sys
import pandas as pd

sys.path.append("/home/diegoximenes/Documents/data_analysis/import_scripts/")
import datetime_procedures, read_input

"""
- description:
	- by now this class represents month univariate time series
- attributes:
	- strdt_mean:
	- x: strdt
	- y: value
"""
class TimeSeries:
	def __init__(self, in_file_path = None, target_month = None, target_year = None, metric = None):
		self.strdt_mean = {}
		self.x = []
		self.y = []

		if in_file_path != None: self.read(in_file_path, target_month, target_year, metric)
				
	def read(self, in_file_path, target_month, target_year, metric):
		self.strdt_mean = read_input.get_strdt_mean(in_file_path, target_month, target_year, metric)
		ts = from_dic_to_list_ts(self.strdt_mean)
		self.x = ts[0]
		self.y = ts[1] 

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
		ts_ret.strdt_mean[ts.x[i]] = val

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
	for i in range(len(ts.y)):
		if ts.y[i] != None:
			ts_ret.x.append(ts.x[i])		
			ts_ret.y.append(ts.y[i])	
		ts_ret.strdt_mean[ts.x[i]] = ts.y[i]
	return ts_ret

"""
- description:
- argument:
- returns: 
"""
def from_dic_to_list_ts(strdt_measure):	
	x, y = [], []
	for strdt in sorted(list(strdt_measure.keys())):
		x.append(strdt)
		y.append(strdt_measure[strdt])
	return [x, y]
