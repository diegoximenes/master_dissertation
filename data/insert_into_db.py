import os
import sys
import datetime
import ast
import pymongo
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures


def insert_into_db_csv(dt_start, dt_end):
    """
    insert into database based on csv info
    """

    date_dir = "dtstart{}_dtend{}".format(dt_start, dt_end)

    client = pymongo.MongoClient()
    collection = client["measurements"]["measurements"]

    collection.create_index([("mac", pymongo.ASCENDING),
                             ("dt", pymongo.ASCENDING),
                             ("server", pymongo.ASCENDING)])

    collection.delete_many({"dt": {"$gte": dt_start, "$lt": dt_end}})

    cnt = 0
    for server in os.listdir("{}/csv/{}".format(script_dir, date_dir)):
        for file_name in os.listdir("{}/csv/{}/{}".format(script_dir, date_dir,
                                                          server)):
            mac = file_name.split(".csv")[0]
            cnt += 1
            print "cnt={}, server={}, mac={}".format(cnt, server, mac)

            df = pd.read_csv("{}/csv/{}/{}/{}".format(script_dir, date_dir,
                                                      server, file_name))
            for idx, row in df.iterrows():
                dic = {}
                dic["mac"] = mac
                dic["server"] = server
                dic["server_ip"] = row["server_ip"]
                dic["dt"] = dt_procedures.from_strdt_to_dt(row["dt"])
                dic["uf"] = row["uf"]
                dic["loss"] = row["loss"]
                dic["traceroute"] = row["traceroute"]
                collection.insert(dic)


def insert_into_db_json(dt_start_sp, dt_end_sp):
    """
    month dump of TGR database
    """

    dt_start = dt_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = dt_procedures.from_sp_to_utc(dt_end_sp)

    client = pymongo.MongoClient()

    collection_measurements = client["measurements"]["measurements"]
    collection_measurements.delete_many({"_id.date": {"$gte": dt_start,
                                                      "$lt": dt_end}})
    collection_measurements.create_index([("_id.mac", pymongo.ASCENDING),
                                          ("_id.date", pymongo.ASCENDING)])

    collection_clients = client["measurements"]["clients"]
    collection_clients.create_index([("mac", pymongo.ASCENDING)], unique=True)

    date_dir = "dtstart{}_dtend{}".format(dt_start_sp, dt_end_sp)
    with open("{}/json/{}.txt".format(script_dir, date_dir)) as f:
        cnt = 0
        for line in f:
            cnt += 1
            print "cnt={}".format(cnt)

            line = line.replace("nan", "None")
            dic = ast.literal_eval(line)
            if ("_id" in dic) and ("date" in dic["_id"]):
                dic["_id"]["date"] = \
                    dt_procedures.from_strdt_to_dt(dic["_id"]["date"])

            collection_measurements.insert(dic)
            if ("_id" in dic) and ("mac" in dic["_id"]):
                dic_mac = {"mac": dic["_id"]["mac"]}
                try:
                    collection_clients.insert(dic_mac)
                except pymongo.errors.DuplicateKeyError:
                    pass


if __name__ == "__main__":
    dt_start_sp = datetime.datetime(2016, 6, 1)
    dt_end_sp = datetime.datetime(2016, 7, 1)
    # insert_into_db_csv(dt_start, dt_end)
    insert_into_db_json(dt_start_sp, dt_end_sp)
