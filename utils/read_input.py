import os
import sys
import pymongo
import pandas as pd
import dt_procedures

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)


def get_raw(in_path, metric, dt_start, dt_end):
    """
    Returns:
        x: sorted datetimes
        y: values, according with x
    """

    l = []
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        if row[metric] != "None":
            dt = dt_procedures.from_strdt_to_dt(row["dt"])
            if dt_procedures.in_dt_range(dt, dt_start, dt_end):
                l.append([dt, float(row[metric])])

    x, y = [], []
    l.sort()
    for p in l:
        x.append(p[0])
        y.append(p[1])

    return x, y


def get_mac_node():
    mac_node = {}
    df = pd.read_csv("{}/input/probes_info.csv".format(base_dir), sep=" ")
    for idx, row in df.iterrows():
        mac_node[row["MAC_ADDRESS"]] = row["NODE"]
    return mac_node


def get_macs():
    client = pymongo.MongoClient()
    collection = client["measurements"]["clients"]
    cursor = collection.find()
    macs = []
    for doc in cursor:
        macs.append(doc["mac"])
    return macs


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


def get_measure(doc, metric):
    def get_loss(doc):
        # check loss existence
        if (("rtt" not in doc) or ("loss" not in doc["rtt"]) or
                ("lat" not in doc["rtt"])):
            return None

        loss = float(doc["rtt"]["loss"])
        # there are some inconsistencies in the database
        if (loss < 0) or (loss > 1):
            return None
        if (loss < 1) and ("s" not in doc["rtt"]["lat"]):
            return None
        return loss

    def get_latency(doc):
        if (("rtt" not in doc) or ("lat" not in doc["rtt"]) or
                ("m" not in doc["rtt"]["lat"])):
            return None
        return doc["rtt"]["lat"]["m"]

    def get_server_ip(doc):
        if "ip" not in doc:
            return None
        return doc["ip"]

    def get_throughput_down(doc):
        if (("thr" not in doc) or ("tcp" not in doc["thr"]) or
                ("down" not in doc["thr"]["tcp"]) or
                ("v" not in doc["thr"]["tcp"]["down"])):
            return None, None
        return doc["thr"]["tcp"]["down"]["v"], doc["thr"]["tcp"]["down"]["n"]

    def get_throughput_up(doc):
        if (("thr" not in doc) or ("tcp" not in doc["thr"]) or
                ("up" not in doc["thr"]["tcp"]) or
                ("v" not in doc["thr"]["tcp"]["up"])):
            return None, None
        return doc["thr"]["tcp"]["up"]["v"], doc["thr"]["tcp"]["up"]["n"]

    def get_traceroute(doc):
        if (("tcrt" not in doc) or ("hops" not in doc["tcrt"])):
            return None
        return doc["tcrt"]["hops"]

    if metric == "loss":
        return get_loss(doc)
    elif metric == "latency":
        return get_latency(doc)
    elif metric == "server_ip":
        return get_server_ip(doc)
    elif metric == "throughput_down":
        return get_throughput_down()
    elif metric == "throughput_up":
        return get_throughput_up()
    elif metric == "traceroute":
        return get_traceroute()


def get_raw_db(mac, metric, dt_start, dt_end):
    """
    if measured to more than one server during [dt_start, dt_end) then
    returns empty lists

    Returns:
        - x: sao paulo datetimes
        - y: measures
        - server: server in which mac measured against during
                  [dt_start, dt_end)
    """

    client = pymongo.MongoClient()
    collection = client["measurements"]["measurements"]
    cursor = collection.find({"$and": [{"_id.date": {"$gte": dt_start,
                                                     "$lt": dt_end}},
                                       {"_id.mac": mac}]})
    x, y = [], []
    servers = set()
    for doc in cursor:
        if valid_doc(doc):
            xi = dt_procedures.from_utc_to_sp(doc["_id"]["date"])
            yi = get_measure(doc, metric)
            serveri = doc["host"]
            if yi is not None:
                servers.add(serveri)
                x.append(xi)
                y.append(yi)

                if len(servers) > 1:
                    return [], [], None
    return x, y, servers.pop()
