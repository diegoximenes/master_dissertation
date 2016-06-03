import os, sys, psycopg2, datetime
import psycopg2.extras

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

def majority_voting(tp, classifications_dt):
	mac, server, date_start = tp[0], tp[1], tp[2]
	target_year, target_month = int(date_start.split("/")[-1]), int(date_start.split("/")[0])
	csv_file_path = "../input/" + str(target_year) + "_" + str(target_month).zfill(2) + "/" + server + "/" + mac + ".csv"
	ts = TimeSeries(csv_file_path, target_month, target_year, metric)
	
	#transform classifications_dt in classifications_id
	dt_id = {}
	for i in xrange(len(ts.raw_x)): dt_id[ts.raw_x[i]] = i
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
	print l
		
def process():
	macServerDtstartDtend_classifications = get_data()
	
	macServerDtstartDtend_correctClassification = {}
	for tp in macServerDtstartDtend_classifications:
		macServerDtstartDtend_correctClassification[tp] = majority_voting(tp, macServerDtstartDtend_classifications[tp])
	print macServerDtstartDtend_correctClassification

process()
