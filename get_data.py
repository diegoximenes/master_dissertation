import os
import sys
from pymongo import MongoClient
from datetime import datetime

base_dir = os.path.join(os.path.dirname(__file__), ".")
sys.path.append(base_dir)

import utils.dt_procedures as dt_procedures
import utils.db_procedures as db_procedures

client = MongoClient("cabul", 27017)
collection = client["NET"]["measures"]


def get_data():
    dt_start_sp = datetime(2016, 7, 1, 0, 0, 0)
    dt_end_sp = datetime(2016, 8, 1, 0, 0, 0)
    target_year, target_month = 2016, 7

    date_dir = "{}_{}".format(target_year, str(target_month).zfill(2))
    dt_start = dt_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = dt_procedures.from_sp_to_utc(dt_end_sp)

    cursor = collection.find({"_id.date": {"$gte": dt_start, "$lt": dt_end}},
                             timeout=False)

    db_procedures.get_data_to_file(cursor, "{}/input/{}/".format(base_dir,
                                                                 date_dir))


if __name__ == "__main__":
    get_data()
