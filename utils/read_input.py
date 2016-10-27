import os
import sys
import ast
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
                yi = row[metric]
                if metric == "traceroute":
                    yi = yi.replace("nan", "None")
                    yi = ast.literal_eval(yi)
                else:
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
