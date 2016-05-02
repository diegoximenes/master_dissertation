import os, sys, shutil
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt

sys.path.append("../import_scripts/")
import datetime_procedures, plot, time_series
from time_series import TimeSeries

target_year, target_month = 2015, 12

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

class DisjointSet:
	def __init__(self, n):
		self.dset = range(n)
	def find(self, i):
		if self.dset[i] == i: return i
		self.dset[i] = self.find(self.dset[i])
		return self.dset[i]
	def same(self, i, j):
		return (self.find(i) == self.find(j))
	def union(self, i, j):
		self.dset[self.find(i)] = self.find(j)
	
def near_change_points(change_points1, change_points2):
	delta_hours = 7

	if len(change_points1) != len(change_points2): return False
	for i in range(len(change_points1)):
		epoch1 = datetime_procedures.from_datetime_to_epoch(change_points1[i])
		epoch2 = datetime_procedures.from_datetime_to_epoch(change_points2[i])
		if abs(epoch1 - epoch2) > 60*60*delta_hours: return False
	return True

def create_dirs():
	if os.path.exists("./plots/") == False:	os.makedirs("./plots/")
	if os.path.exists("./plots/changepoint") == False: os.makedirs("./plots/changepoint")
	if os.path.exists("./plots/changepoint/" + date_dir): shutil.rmtree("./plots/changepoint/" + date_dir)
	os.makedirs("./plots/changepoint/" + date_dir)

def cross_change_points():
	mac_dtChangePoints = {}
	mac_server = {}

	for server in os.listdir("./change_points/" + date_dir):	
		print server
		for file_name in os.listdir("./change_points/" + date_dir + "/" + server + "/"):
			print file_name
			mac = file_name.split(".")[0]
			mac_server[mac] = server
						
			dt_change_points = []
			df = pd.read_csv("./change_points/" + date_dir + "/" + server + "/" + file_name)
			for idx, row in df.iterrows():
				dt = datetime_procedures.from_strDatetime_to_datetime(row["datetime"])
				dt_change_points.append(dt)
			
			if mac in mac_dtChangePoints: print "mac " + mac + " measured to more than one server"
			elif len(dt_change_points) >= 2: mac_dtChangePoints[mac] = dt_change_points[0 : len(dt_change_points) - 1]
	
	macs_list = []
	for mac in mac_dtChangePoints: macs_list.append(mac)
		
	dset = DisjointSet(len(macs_list))
	
	for i in range(len(macs_list)):
		for j in range(i+1, len(macs_list)):
			mac1, mac2 = macs_list[i], macs_list[j]
			if near_change_points(mac_dtChangePoints[mac1], mac_dtChangePoints[mac2]):
				dset.union(i, j)
				#print "mac1=" + mac1 + ", change_points1=" + str(mac_dtChangePoints[mac1]) + ", mac2=" + mac2 + ", change_points2=" + str(mac_dtChangePoints[mac2])
	
	create_dirs()
	
	dsetId_macs = {}
	for i in range(len(macs_list)):
		dset_id = dset.find(i)	
		if dset_id not in dsetId_macs: dsetId_macs[dset_id] = []
		dsetId_macs[dset_id].append(macs_list[i])

	for dset_id in dsetId_macs:
		print "dset_id=" + str(dset_id) + ", macs=" + str(dsetId_macs[dset_id])
		os.makedirs("./plots/changepoint/" + date_dir + "/" + str(dset_id))
		for mac in dsetId_macs[dset_id]:
			in_file_path = "./input/" + date_dir + "/" + mac_server[mac] + "/" + mac + ".csv"
			out_file_path = "./plots/changepoint/" + date_dir + "/" + str(dset_id) + "/" + mac + "_" + mac_server[mac] + ".png"
			ts = TimeSeries(in_file_path, target_month, target_year, "loss")
			
			plot.plot_ts(ts, out_file_path, mac_dtChangePoints[mac], "loss", [-0.02, 1.02])

cross_change_points()
