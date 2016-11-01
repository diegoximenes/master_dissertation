import os
import sys
from pymongo import MongoClient
from datetime import datetime

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
import utils.utils as utils


def create_dirs(dt_dir, server):
    for dir in ["{}/{}".format(script_dir, dt_dir),
                "{}/{}/{}/".format(script_dir, dt_dir, server)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def valid_doc(doc):
    # check mac, date existence
    if (("_id" not in doc) or ("mac" not in doc["_id"]) or
            ("date" not in doc["_id"])):
        return False

    # check server(host), carrier(ISP), uf(client uf), huf(server uf) existence
    if (("host" not in doc) or ("carrier" not in doc) or
            ("uf" not in doc) or ("huf" not in doc)):
        return False

    if doc["carrier"] != "NET":
        return False

    # client and server must have the same uf
    if doc["uf"] != doc["huf"]:
        return False

    return True


def get_server_ip(doc):
    if "ip" not in doc:
        return None
    return doc["ip"]


def get_loss(doc):
    # check loss existence
    if (("rtt" not in doc) or ("loss" not in doc["rtt"]) or
            ("lat" not in doc["rtt"]) or ("xtrf" not in doc["rtt"]) or
            ("u" not in doc["rtt"]["xtrf"]) or
            ("d" not in doc["rtt"]["xtrf"])):
        return None, None, None

    loss = float(doc["rtt"]["loss"])
    # there are some inconsistencies in the database
    if (loss < 0) or (loss > 1):
        return None, None, None
    if (loss < 1) and ("s" not in doc["rtt"]["lat"]):
        return None, None, None

    return loss, doc["rtt"]["xtrf"]["u"], doc["rtt"]["xtrf"]["d"]


def get_latency(doc):
    if (("rtt" not in doc) or ("lat" not in doc["rtt"]) or
            ("m" not in doc["rtt"]["lat"]) or ("xtrf" not in doc["rtt"]) or
            ("u" not in doc["rtt"]["xtrf"]) or
            ("d" not in doc["rtt"]["xtrf"])):
        return None, None, None
    return (doc["rtt"]["lat"]["m"], doc["rtt"]["xtrf"]["u"],
            doc["rtt"]["xtrf"]["d"])


def get_throughput_down(doc):
    if (("thr" not in doc) or ("tcp" not in doc["thr"]) or
            ("down" not in doc["thr"]["tcp"]) or
            ("v" not in doc["thr"]["tcp"]["down"]) or
            ("xtrf" not in doc["thr"]["tcp"]["down"]) or
            ("u" not in doc["thr"]["tcp"]["down"]["xtrf"]) or
            ("d" not in doc["thr"]["tcp"]["down"]["xtrf"])):
        return None, None, None, None
    return (doc["thr"]["tcp"]["down"]["v"], doc["thr"]["tcp"]["down"]["n"],
            doc["thr"]["tcp"]["down"]["xtrf"]["u"],
            doc["thr"]["tcp"]["down"]["xtrf"]["d"])


def get_throughput_up(doc):
    if (("thr" not in doc) or ("tcp" not in doc["thr"]) or
            ("up" not in doc["thr"]["tcp"]) or
            ("v" not in doc["thr"]["tcp"]["up"]) or
            ("xtrf" not in doc["thr"]["tcp"]["up"]) or
            ("u" not in doc["thr"]["tcp"]["up"]["xtrf"]) or
            ("d" not in doc["thr"]["tcp"]["up"]["xtrf"])):
        return None, None, None, None
    return (doc["thr"]["tcp"]["up"]["v"], doc["thr"]["tcp"]["up"]["n"],
            doc["thr"]["tcp"]["up"]["xtrf"]["u"],
            doc["thr"]["tcp"]["up"]["xtrf"]["d"])


def get_traceroute(doc):
    if (("tcrt" not in doc) or ("hops" not in doc["tcrt"])):
        return None
    return doc["tcrt"]["hops"]


def get_macs(cursor):
    """
    only consider clients that measured against a single server in the cursor
    documents. Returns a list with the macs and another one with the associated
    servers
    """

    mac_servers = {}
    cnt = 0
    for doc in cursor:
        cnt += 1
        print "get_macs, cnt={}".format(cnt)

        if not valid_doc(doc):
            continue

        mac = doc["_id"]["mac"]
        server = doc["host"]

        if mac not in mac_servers:
            mac_servers[mac] = set()
        mac_servers[mac].add(server)

    macs = []
    servers = []
    for mac in mac_servers:
        if len(mac_servers[mac]) == 1:
            macs.append(mac)
            servers.append(mac_servers[mac].pop())
    return macs, servers


def write_csvs(dt_dir, dt_start, dt_end, cursor, collection):
    macs, servers = get_macs(cursor)

    cnt = 0
    for mac, server in zip(macs, servers):
        cnt += 1
        print "mac={}, cnt={}".format(mac, cnt)

        create_dirs(dt_dir, server)

        cursor = collection.find({"$and": [{"_id.date": {"$gte": dt_start,
                                                         "$lt": dt_end}},
                                           {"_id.mac": mac}]})
        out_path = "{}/{}/{}/{}.csv".format(script_dir, dt_dir, server,
                                            mac)
        with open(out_path, "w") as f:
            f.write("dt,uf,server_ip,loss,latency,throughput_up,"
                    "throughput_down,nominal_up,nominal_down,"
                    "loss_cross_traffic_up,loss_cross_traffic_down,"
                    "latency_cross_traffic_up,latency_cross_traffic_down,"
                    "throughput_up_cross_traffic_up,"
                    "throughput_up_cross_traffic_down,"
                    "throughput_down_cross_traffic_up,"
                    "throughput_down_cross_traffic_down,"
                    "traceroute\n")

            for doc in cursor:
                if (not valid_doc(doc)):
                    continue

                uf = doc["uf"]
                server = doc["host"]
                dt = dt_procedures.from_utc_to_sp(doc["_id"]["date"])
                server_ip = get_server_ip(doc)

                (loss, loss_cross_traffic_up, loss_cross_traffic_down) = \
                    get_loss(doc)

                (latency, latency_cross_traffic_up,
                 latency_cross_traffic_down) = get_latency(doc)

                (throughput_up, nominal_up,
                 throughput_up_cross_traffic_up,
                 throughput_up_cross_traffic_down) = get_throughput_up(doc)

                (throughput_down, nominal_down,
                 throughput_down_cross_traffic_up,
                 throughput_down_cross_traffic_down) = get_throughput_down(doc)

                traceroute = get_traceroute(doc)

                l = "{}" + ",{}" * 16 + ",\"{}\"\n"
                f.write(l.format(dt,
                                 uf,
                                 server_ip,
                                 loss,
                                 latency,
                                 throughput_up,
                                 throughput_down,
                                 nominal_up,
                                 nominal_down,
                                 loss_cross_traffic_up,
                                 loss_cross_traffic_down,
                                 latency_cross_traffic_up,
                                 latency_cross_traffic_down,
                                 throughput_up_cross_traffic_up,
                                 throughput_up_cross_traffic_down,
                                 throughput_down_cross_traffic_up,
                                 throughput_down_cross_traffic_down,
                                 traceroute))


def get_data(dt_start_sp, dt_end_sp):
    """
    [dt_start_sp, dt_end_sp) must define a month
    """

    dt_dir = utils.get_dt_dir(dt_start_sp, dt_end_sp)

    client = MongoClient("cabul", 27017)
    collection = client["NET"]["measures"]

    dt_start = dt_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = dt_procedures.from_sp_to_utc(dt_end_sp)

    cursor = collection.find({"_id.date": {"$gte": dt_start, "$lt": dt_end}})
    write_csvs(dt_dir, dt_start, dt_end, cursor, collection)


if __name__ == "__main__":
    # dt_start_sp = datetime(2016, 10, 1, 0, 0, 0)
    # dt_end_sp = datetime(2016, 11, 1, 0, 0, 0)
    # get_data(dt_start_sp, dt_end_sp)

    for month in range(7, 10):
        dt_start_sp = datetime(2016, month, 1)
        dt_end_sp = datetime(2016, month + 1, 1)
        get_data(dt_start_sp, dt_end_sp)
