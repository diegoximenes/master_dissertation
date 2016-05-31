import psycopg2
import pandas as pd

host_version = "local"
#host_version = "trindade"
in_file_path = "ts_to_be_inserted.csv"

try: 
	conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' user='postgres' host='localhost' password='admin'")
	conn.autocommit = True
except: 
	print "unable to connect to the database"
	sys.exit(0)
cursor = conn.cursor()

def insert_into_db():
	df = pd.read_csv(in_file_path)
	for idx, row in df.iterrows():
		csv_path = row["csv_path"]
		if host_version == "trindade": 
			year = row["date_start"].split("/")[-1]
			month = row["date_start"].split("/")[0]
			csv_path = "/home/localuser/diegoximenes_mestrado/change_point_detection/input/" + str(year) + "_" + str(month).zfill(2) + "/" + row["server"] + "/" + row["mac"] + ".csv"
		sql = "INSERT INTO time_series(mac, server, csv_path, date_start, date_end) VALUES('%s', '%s', '%s', '%s', '%s')"%(row["mac"], row["server"], csv_path, row["date_start"], row["date_end"])
		try: cursor.execute(sql)
		except: 
			print "error on insertion: " + sql
			sys.exit(0)

insert_into_db()
