import psycopg2, os, sys, calendar, datetime
import psycopg2.extras
import pandas as pd

sys.path.append("../../../import_scripts/")
import datetime_procedures, time_series, plot_procedures
from time_series import TimeSeries

#parameters
target_year, target_month = 2016, 5
metric = "loss"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def create_dirs_server(server):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/per_server") == False: os.makedirs("./plots/per_server/")
	if os.path.exists("./plots/per_server/" + server) == False: os.makedirs("./plots/per_server/" + server)
def create_dirs_user(user):
	if os.path.exists("./plots/") == False: os.makedirs("./plots/")
	if os.path.exists("./plots/per_user/") == False: os.makedirs("./plots/per_user/")
	if os.path.exists("./plots/per_user/" + user) == False: os.makedirs("./plots/per_user/" + user)

def get_data():
	try: 
		conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' user='postgres' host='localhost' password='admin'")
		conn.autocommit = True
	except: 
		print "unable to connect to the database"
		sys.exit(0)
	cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

	cursor.execute("""SELECT users.email, time_series.mac, time_series.server, time_series.date_start, time_series.date_end, change_points.change_points FROM users, time_series, change_points WHERE (change_points.id_user = users.id) AND (change_points.id_time_series = time_series.id)""")
	for row in cursor.fetchall():
		dt_cp_list = []
		if row["change_points"] != "":
			for strdt in row["change_points"].split(","):
				str_date = strdt.split("T")[0]
				str_time = strdt.split("T")[1].split(".")[0]
				dt = datetime.datetime(int(str_date.split("-")[0]), int(str_date.split("-")[1]), int(str_date.split("-")[2]), int(str_time.split(":")[0]), int(str_time.split(":")[1]), int(str_time.split(":")[2]))
				dt_sp = datetime_procedures.from_utc_to_sp(dt)
				dt = datetime.datetime(dt_sp.year, dt_sp.month, dt_sp.day, dt_sp.hour, dt_sp.minute)
				dt_cp_list.append(dt)
		
		create_dirs_server(row["server"])	
		create_dirs_user(row["email"])
		
		in_file_path = "../../input/" + date_dir + "/" + row["server"] + "/" + row["mac"] + ".csv"
		ts = TimeSeries(in_file_path, target_month, target_year, metric)

		out_file_path = "./plots/per_server/" + row["server"] + "/" + row["mac"] + "_" + row["email"] + ".png"
		plot_procedures.plot_ts(ts, out_file_path , ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp_list)

		out_file_path = "./plots/per_user/" + row["email"] + "/" + row["server"] + "_" + row["mac"] + ".png"
		plot_procedures.plot_ts(ts, out_file_path , ylabel = "loss", ylim = [-0.02, 1.02], dt_axvline = dt_cp_list)

get_data()
