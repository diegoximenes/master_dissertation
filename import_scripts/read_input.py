import os, ast, sys
import pandas as pd

import datetime_procedures

"""
- description:
	- returns a dic in which the keys are each hour of the target month and the value is the mean of the specified hour
- arguments
- returns:
	- dic:
		- key: strdt
		- value: mean of measures in strdt bin
"""
def get_strdt_mean(in_file_path, target_month, target_year, metric):
	strdt_bin = datetime_procedures.generate_hourly_bins_month([target_month, target_year])
	
	strdt_cntSum = {}
	for strdt in strdt_bin: strdt_cntSum[strdt] = [0, 0]
	
	df = pd.read_csv(in_file_path)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		strdt = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2) + " " + str(dt.hour).zfill(2) + ":00:00"
		
		if strdt not in strdt_cntSum: continue
		
		strdt_cntSum[strdt][0] += 1
		strdt_cntSum[strdt][1] += row[metric]
	
	strdt_mean = {}
	for strdt in strdt_cntSum:
		if strdt_cntSum[strdt][0] > 0: strdt_mean[strdt] = float(strdt_cntSum[strdt][1])/strdt_cntSum[strdt][0]
		else: strdt_mean[strdt] = None

	return strdt_mean


############################################################################################
############################################################################################
#LEGACY CODE
############################################################################################
############################################################################################

def read_server_uf_ip():
	server_uf, server_ip = {}, {}
	df = pd.read_csv("../input/net_server_uf.csv")
	for index, row in df.iterrows():
		server_ip[row["name"]] = row["ip"]
		server_uf[row["name"]] = row["uf"]
	return server_uf, server_ip

def read_mac_uf():
	mac_uf = {}
	file = open("../input/probe_ufs.txt")
	for line in file: mac_uf[line.split()[0]] = line.split()[1]
	file.close()
	return mac_uf

def read_mac_nominal():
	mac_up, mac_down = {}, {}
	df = pd.read_csv("../input/mac_nominal_capacity.csv")
	for index, row in df.iterrows():
		mac_up[row["mac"]] = row["up"]
		mac_down[row["mac"]] = row["down"]
	return mac_up, mac_down

def read_mac_provider():
	mac_provider = {}
	df = pd.read_csv("../input/mac_provider.csv", sep = ";")
	for index, row in df.iterrows(): mac_provider[row["MAC_ADDRESS"]] = row["CARRIER"]
	return mac_provider

def mac_roundedDatetimeMeasure(in_dir):
	mac_datetimeMeasure = {}	

	for file_name in os.listdir(in_dir):
		server = file_name.split(".")[0]
		file = open(in_dir + file_name)
		for line in file:
			splitted = line.split()
			mac = splitted[0]
			datetime_measure = ast.literal_eval(' '.join(splitted[1:]))
			
			if mac not in mac_datetimeMeasure: mac_datetimeMeasure[mac] = []
				
			for str_datetime in datetime_measure: mac_datetimeMeasure[mac].append([datetime_procedures.get_rounded_strDatetime(str_datetime), datetime_measure[str_datetime]])

	for mac in mac_datetimeMeasure: mac_datetimeMeasure[mac].sort()
	
	return mac_datetimeMeasure
