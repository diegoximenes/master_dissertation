import psycopg2
import pandas as pd

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
		sql = "INSERT INTO time_series(mac, server, csv_path, date_start, date_end) VALUES('%s', '%s', '%s', '%s', '%s')"%(row["mac"], row["server"], row["csv_path"], row["date_start"], row["date_end"])
		try: cursor.execute(sql)
		except: 
			print "error on insertion: " + sql
			sys.exit(0)

insert_into_db()
