import os, sys, psycopg2, datetime
import psycopg2.extras
import pandas as pd

sys.path.append("../../import_scripts/")
import datetime_procedures, time_series, plot_procedures
from time_series import TimeSeries

metric = "loss"

def get_datetime(strdt_js):
	strdate = strdt_js.split("T")[0]
	strtime = strdt_js.split("T")[1].split(".000")[0]
	dt = datetime.datetime(int(strdate.split("-")[0]), int(strdate.split("-")[1]), int(strdate.split("-")[2]), int(strtime.split(":")[0]), int(strtime.split(":")[1]), int(strtime.split(":")[2]))
	dt_sp = datetime_procedures.from_utc_to_sp(dt)
	dt_ret = datetime.datetime(dt_sp.year, dt_sp.month, dt_sp.day, dt_sp.hour, dt_sp.minute, dt_sp.second)
	#print "dt=" + str(dt) + ", dt_sp=" + str(dt_sp) + "dt_sp.hour=" + str(dt_sp.hour) + "dt_ret=" + str(dt_ret)
	return dt_ret

def get_data():
	try: 
		conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' user='postgres' host='localhost' password='admin'")
		conn.autocommit = True
	except: 
		print "unable to connect to the database"
		sys.exit(0)
	cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
	
	macServerDtstartDtend_classifications = {}

	cursor.execute("""SELECT users.email, time_series.mac, time_series.server, time_series.date_start, time_series.date_end, change_points.change_points FROM users, time_series, change_points WHERE (change_points.id_user = users.id) AND (change_points.id_time_series = time_series.id)""")
	for row in cursor.fetchall():
		dt_cp_list = []
		for strdt_js in row["change_points"].split(","):
			if strdt_js != "":
				dt = get_datetime(strdt_js)
				dt_cp_list.append(dt)
		
		tp = (row["mac"], row["server"], row["date_start"], row["date_end"]) 
		if tp not in macServerDtstartDtend_classifications: macServerDtstartDtend_classifications[tp] = []
		macServerDtstartDtend_classifications[tp].append(dt_cp_list)

	return macServerDtstartDtend_classifications

def create_dirs(mac, server, date_start, date_end):
	if os.path.exists("./majority_voting/") == False: os.makedirs("./majority_voting/")
	dir_path = "./majority_voting/" + "mac_" + mac + "_server" + server + "_datestart" + date_start.replace("/", "-") + "_dateend" + date_end.replace("/", "-") + "/"
	if os.path.exists(dir_path) == False: os.makedirs(dir_path)
	return dir_path

def majority_voting(tp, classifications_dt):
	delta = 5
	min_fraction_of_votes = 0.5
	
	mac, server, date_start, date_end = tp[0], tp[1], tp[2], tp[3]
	dt_start = datetime.datetime(int(date_start.split("/")[2]), int(date_start.split("/")[0]), int(date_start.split("/")[1]))
	dt_end = datetime.datetime(int(date_end.split("/")[2]), int(date_end.split("/")[0]), int(date_end.split("/")[1]))
	target_year, target_month = int(date_start.split("/")[-1]), int(date_start.split("/")[0])
	csv_file_path = "../input/" + str(target_year) + "_" + str(target_month).zfill(2) + "/" + server + "/" + mac + ".csv"
	ts = TimeSeries(csv_file_path, target_month, target_year, metric, dt_start = dt_start, dt_end = dt_end)
	
	#transform classifications_dt in classifications_id
	dt_id, id_dt = {}, {}
	for i in xrange(len(ts.raw_x)): dt_id[ts.raw_x[i]], id_dt[i] = i, ts.raw_x[i]
	classifications_id = []
	for class_dt in classifications_dt:
		class_id = []
		for dt in class_dt: class_id.append(dt_id[dt])
		classifications_id.append(class_id)
	
	l = []
	for user_id in xrange(len(classifications_id)):
		for id in classifications_id[user_id]:
			l.append([id, user_id])
	l.sort()

	#by now disconsider that a user can set change points too close. by now only get the left point
	classification_out = []
	n_users = len(classifications_id)
	while len(l) > 0:
		for i in xrange(1, len(l)):
			if l[i][0] - l[0][0] > delta:
				if float(i)/n_users >= min_fraction_of_votes: classification_out.append(l[0][0])
				l = l[i:]
				break
		if l[-1][0] - l[0][0] <= delta:
			if float(i)/n_users >= min_fraction_of_votes: classification_out.append(l[0][0])
			l = []
	
	#plot
	out_dir_path = create_dirs(mac, server, date_start, date_end)
	for i in xrange(len(classifications_dt)): 
		plot_procedures.plot_ts(ts, out_dir_path + "/user" + str(i) + ".png", ylim = [-0.01, 1.01], dt_axvline = classifications_dt[i], compressed = True)
	class_dt_out = []
	for id in classification_out: class_dt_out.append(id_dt[id])
	plot_procedures.plot_ts(ts, out_dir_path + "/correct.png", ylim = [-0.01, 1.01], dt_axvline = class_dt_out, compressed = True)
	
	return classification_out
		
def process():
	macServerDtstartDtend_classifications = get_data()
	
	macServerDtstartDtend_correctClassification = {}
	for tp in macServerDtstartDtend_classifications:
		macServerDtstartDtend_correctClassification[tp] = majority_voting(tp, macServerDtstartDtend_classifications[tp])
	

def process_test_tgr():
	macServerDtstartDtend_classifications = {}
	
	#get data
	df = pd.read_csv("./majority_voting_data.csv", sep = ";")
	for idx, row in df.iterrows():
		dt_cp_list = []
		tp = (row["mac"], row["server"], row["date_start"], row["date_end"]) 
		if tp not in macServerDtstartDtend_classifications: macServerDtstartDtend_classifications[tp] = []
		if row["change_points"] != "\'\'":
			for strdt_js in row["change_points"].split(","):
				if strdt_js != "":
					dt = get_datetime(strdt_js)
					dt_cp_list.append(dt)
		macServerDtstartDtend_classifications[tp].append(dt_cp_list)

	macServerDtstartDtend_correctClassification = {}
	for tp in macServerDtstartDtend_classifications:
		macServerDtstartDtend_correctClassification[tp] = majority_voting(tp, macServerDtstartDtend_classifications[tp])

#process()
process_test_tgr()
