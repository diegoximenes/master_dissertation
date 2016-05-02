from pymongo import MongoClient
import pytz, os, sys, calendar
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt
import numpy as np

sys.path.append("/home/diegoximenes/Documents/data_analysis/import_scripts/")
import datetime_procedures, read_input, database

client = MongoClient("cabul", 27017)
db = client["NET"]
collection = db["measures"]

begin_dt_sp = datetime(2016, 3, 1, 0, 0, 0)
end_dt_sp = datetime(2016, 4, 1, 0, 0, 0)
target_year, target_month = 2016, 3

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def process():
	begin_dt = datetime_procedures.from_sp_to_utc(begin_dt_sp)
	end_dt = datetime_procedures.from_sp_to_utc(end_dt_sp)
	
	cursor = collection.find({"$and" : [{"_id.date": {"$gte" : begin_dt}}, {"_id.date" : {"$lt" : end_dt}}]})
	
	database.get_data_to_file(cursor, "./input/" + date_dir + "/")

process()
