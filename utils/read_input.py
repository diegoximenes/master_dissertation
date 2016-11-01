import os
import sys
import ast
import pandas as pd
import dt_procedures

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils


def valid_row(metric, row, cross_traffic_thresh):
    if (metric == "traceroute") or (metric == "server_ip"):
        return row[metric] != "None"

    if ((row[metric] == "None") or
            (row[metric + "_cross_traffic_up"] == "None") or
            (row[metric + "_cross_traffic_down"] == "None")):
        return False

    if ((float(row[metric + "_cross_traffic_up"]) > cross_traffic_thresh) or
            (float(row[metric + "_cross_traffic_down"]) >
             cross_traffic_thresh)):
        return False
    return True


def get_raw(in_path, metric, dt_start, dt_end, cross_traffic_thresh):
    """
    Returns:
        x: sorted datetimes
        y: values, according with x
    """

    l = []
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        if valid_row(metric, row, cross_traffic_thresh):
            dt = dt_procedures.from_strdt_to_dt(row["dt"])
            if dt_procedures.in_dt_range(dt, dt_start, dt_end):
                yi = row[metric]
                if metric == "traceroute":
                    yi = yi.replace("nan", "None")
                    yi = ast.literal_eval(yi)
                elif metric != "server_ip":
                    yi = float(yi)
                l.append([dt, yi])

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


def get_valid_nodes():
    df = pd.read_csv("{}/change_point/unsupervised/prints/valid_nodes.csv".
                     format(base_dir))
    valid_nodes = set()
    for idx, row in df.iterrows():
        valid_nodes.add(row["node"])
    return valid_nodes


def get_macs_traceroute_filter(dt_start, dt_end, filtered):
    """
    returns macs that have an unique traceroute in [dt_start, dt_end) in a set
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)
    in_path = ("{}/change_point/unsupervised/prints/{}/{}/"
               "traceroute_per_mac.csv".format(base_dir, str_dt, filtered))
    macs = set()
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        macs.add(row["mac"])
    return macs
