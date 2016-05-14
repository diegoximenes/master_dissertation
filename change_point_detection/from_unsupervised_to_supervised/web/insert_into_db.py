import psycopg2, os, sys, calendar, datetime
import pandas as pd

sys.path.append("../../../import_scripts/")
import datetime_procedures

#parameters
target_year, target_month = 2015, 12
min_fraction_of_measures = 0.4
time_range_type = "month"
#time_range_type, len_day_range = "day_range", 7

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def has_enough_data(file_path, date_start, date_end):
	cnt = 0
	dt_start = datetime.datetime(int(date_start.split("/")[2]), int(date_start.split("/")[0]), int(date_start.split("/")[1]))
	dt_end = datetime.datetime(int(date_end.split("/")[2]), int(date_end.split("/")[0]), int(date_end.split("/")[1]))
	df = pd.read_csv(file_path)
	for idx, row in df.iterrows():
		dt = datetime_procedures.from_strDatetime_to_datetime(row["dt"])
		if dt <= dt_end and dt >= dt_start:
			cnt += 1
	
	max_number_of_measures = 48*(dt_end - dt_start).days
	if(float(cnt)/max_number_of_measures >= min_fraction_of_measures): return True
	return False

try: 
	conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' user='postgres' host='localhost' password='admin'")
	conn.autocommit = True
except: 
	print "unable to connect to the database"
	sys.exit(0)

cursor = conn.cursor()

month_date_start = str(target_month).zfill(2) + "/01/" + str(target_year)
month_date_end = str(target_month).zfill(2) + "/" + str(calendar.monthrange(target_year, target_month)[-1]).zfill(2) + "/" + str(target_year)

in_dir = "../../input/" + date_dir
for server in os.listdir(in_dir):
	for file_name in os.listdir(in_dir + "/" + server + "/"): 
		mac = file_name.split(".")[0]
		csv_path = in_dir + "/" + server + "/" + file_name
	
		if time_range_type == "month":
			if has_enough_data(csv_path, month_date_start, month_date_end) == False: continue

			sql = "INSERT INTO time_series(mac, server, csv_path, date_start, date_end) VALUES('%s', '%s', '%s', '%s', '%s')"%(mac, server, csv_path, month_date_start, month_date_end)
			try: cursor.execute(sql)
			except: 
				print "error on insertion: " + sql
				sys.exit(0)
		elif time_range_type == "day_range":
			for day_start in range(1, calendar.monthrange(target_year, target_month)[-1] + 1, len_day_range):
				if day_start + len_day_range-1 >  calendar.monthrange(target_year, target_month)[-1]: break
				
				date_start = str(target_month).zfill(2) + "/" + str(day_start).zfill(2) + "/" + str(target_year)
				date_end = str(target_month).zfill(2) + "/" + str(day_start + len_day_range - 1).zfill(2) + "/" + str(target_year)
				
				if has_enough_data(csv_path, date_start, date_end) == False: continue
			
				sql = "INSERT INTO time_series(mac, server, csv_path, date_start, date_end) VALUES('%s', '%s', '%s', '%s', '%s')"%(mac, server, csv_path, date_start, date_end)
				try: cursor.execute(sql)
				except: 
					print "error on insertion: " + sql
					sys.exit(0)
