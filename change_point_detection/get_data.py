from pymongo import MongoClient
import sys
from datetime import datetime

sys.path.append("../import_scripts/")
import datetime_procedures
import database

client = MongoClient("cabul", 27017)
db = client["NET"]
collection = db["measures"]

dt_start_sp = datetime(2016, 3, 1, 0, 0, 0)
dt_end_sp = datetime(2016, 4, 1, 0, 0, 0)
target_year, target_month = 2016, 3

date_dir = "{}_{}".format(target_year, str(target_month).zfill(2))


def process():
    dt_start = datetime_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = datetime_procedures.from_sp_to_utc(dt_end_sp)

    cursor = collection.find({"$and": [{"_id.date": {"$gte": dt_start}},
                                       {"_id.date": {"$lt": dt_end}}]})

    database.get_data_to_file(cursor, "./input/" + date_dir + "/")

process()
