import os
import sys
from pymongo import MongoClient
from datetime import datetime

base_dir = os.path.join(os.path.dirname(__file__), ".")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
import utils.db_procedures as db_procedures


def create_dirs(date_dir, server):
    for dir in ["{}/input/".format(base_dir),
                "{}/input/{}".format(base_dir, date_dir),
                "{}/input/{}/{}/".format(base_dir, date_dir, server)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def get_data(dt_start_sp, dt_end_sp):
    """
    dt_start_sp and dt_end_sp must define a month in sao paulo time
    """

    target_year = dt_start_sp.year
    target_month = dt_start_sp.month

    client = MongoClient("cabul", 27017)
    collection = client["NET"]["measures"]

    date_dir = "{}_{}".format(target_year, str(target_month).zfill(2))
    dt_start = dt_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = dt_procedures.from_sp_to_utc(dt_end_sp)

    cursor = collection.find({"_id.date": {"$gte": dt_start, "$lt": dt_end}})
    macs, servers = db_procedures.get_macs(cursor)

    cnt = 0
    for mac, server in zip(macs, servers):
        cnt += 1
        print "mac={}, cnt={}".format(mac, cnt)

        create_dirs(date_dir, server)

        cursor = collection.find({"$and": [{"_id.date": {"$gte": dt_start,
                                                         "$lt": dt_end}},
                                           {"_id.mac": mac}]})
        out_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir, server,
                                                  mac)
        with open(out_path, "w") as f:
            f.write("dt,uf,server_ip,loss,traceroute\n")

            for doc in cursor:
                if ((not db_procedures.valid_doc(doc)) or
                        (not db_procedures.valid_doc_loss(doc))):
                    continue

                uf = doc["uf"]
                server = doc["host"]
                dt = dt_procedures.from_utc_to_sp(doc["_id"]["date"])
                loss = float(doc["rtt"]["loss"])

                if "ip" in doc:
                    server_ip = doc["ip"]
                else:
                    server_ip = None

                if db_procedures.valid_doc_traceroute(doc):
                    traceroute = doc["tcrt"]["hops"]
                else:
                    traceroute = None

                f.write("{},{},{},{},\"{}\"\n".format(dt, uf, server_ip, loss,
                                                      traceroute))

if __name__ == "__main__":
    # dt_start_sp = datetime(2016, 8, 1, 0, 0, 0)
    # dt_end_sp = datetime(2016, 9, 1, 0, 0, 0)
    # get_data(dt_start_sp, dt_end_sp)

    for month in range(6, 10):
        dt_start_sp = datetime(2016, month, 1, 0, 0, 0)
        dt_end_sp = datetime(2016, month + 1, 1, 0, 0, 0)
        get_data(dt_start_sp, dt_end_sp)
