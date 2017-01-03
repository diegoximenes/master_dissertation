import os
import sys
import datetime
import shutil
from pymongo import MongoClient

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils


def valid_doc(doc):
    # check mac, date existence
    if (("_id" not in doc) or ("mac" not in doc["_id"]) or
            ("date" not in doc["_id"])):
        return False

    # check server(host), carrier(ISP) existence
    if ("host" not in doc) or ("carrier" not in doc):
        return False
    if doc["carrier"] != "NET":
        return False

    # check uf(client uf), huf(server uf) existence
    # if ("uf" not in doc) or ("huf" not in doc):
    #     return False
    # # client and server must have the same uf
    # if doc["uf"] != doc["huf"]:
    #     return False

    return True


def get_uf(doc):
    if "uf" not in doc:
        return None
    return doc["uf"]


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


def write_csvs(dt_dir, dt_start, dt_end, cursor, collection):
    for cnt, doc in enumerate(cursor):
        print "{}, {}".format(cnt, utils.get_str_dt(dt_start, dt_end))
        if valid_doc(doc):
            mac = doc["_id"]["mac"]
            server = doc["host"]

            utils.create_dirs(["{}/{}".format(script_dir, dt_dir),
                               "{}/{}/{}/".format(script_dir, dt_dir, server)])

            out_path = "{}/{}/{}/{}.csv".format(script_dir, dt_dir, server,
                                                mac)

            if not os.path.exists(out_path):
                with open(out_path, "w") as f:
                    l = ("dt,uf,server_ip,loss,latency,throughput_up,"
                         "throughput_down,nominal_up,nominal_down,"
                         "loss_cross_traffic_up,loss_cross_traffic_down,"
                         "latency_cross_traffic_up,latency_cross_traffic_down,"
                         "throughput_up_cross_traffic_up,"
                         "throughput_up_cross_traffic_down,"
                         "throughput_down_cross_traffic_up,"
                         "throughput_down_cross_traffic_down,"
                         "traceroute\n")
                    f.write(l)

            uf = get_uf(doc)
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
            l = l.format(dt,
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
                         traceroute)
            with open(out_path, "a") as f:
                f.write(l)


def get_data(dt_start_sp, dt_end_sp):
    """
    [dt_start_sp, dt_end_sp) must define a month
    """

    dt_dir = utils.get_dt_dir(dt_start_sp, dt_end_sp)

    out_dir = "{}/{}".format(script_dir, dt_dir)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)

    client = MongoClient("cabul", 27017)
    collection = client["NET"]["measures"]

    dt_start = dt_procedures.from_sp_to_utc(dt_start_sp)
    dt_end = dt_procedures.from_sp_to_utc(dt_end_sp)

    cursor = collection.find({"_id.date": {"$gte": dt_start, "$lt": dt_end}})
    write_csvs(dt_dir, dt_start, dt_end, cursor, collection)


def iter_dt_months():
    for month in range(5, 12):
        dt_start = datetime.datetime(2016, month, 1)
        dt_end = datetime.datetime(2016, month + 1, 1)
        yield dt_start, dt_end
    dt_start = datetime.datetime(2016, 12, 1)
    dt_end = datetime.datetime(2017, 1, 1)
    yield dt_start, dt_end


# ALERT: parallel is not working in this script...i dont know why

def run_sequential():
    for dt_start, dt_end in iter_dt_months():
        get_data(dt_start, dt_end)


def run_single(dt_start, dt_end):
    get_data(dt_start, dt_end)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 6, 1)

    sequential_args = {}
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    cp_utils.parse_args(run_single, single_args,
                        None, None,
                        run_sequential, sequential_args,
                        None, None)
