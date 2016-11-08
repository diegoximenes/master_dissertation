import os
import sys
import ast
import datetime
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def get_graph(dt_start, dt_end, server):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)

    name_neigh = {}
    df = pd.read_csv(in_path)
    df = df[df["server"] == server]
    for idx, row in df.iterrows():
        traceroute = ast.literal_eval(row["traceroute_filtered"])
        last_name = None
        for name in traceroute:
            if name not in name_neigh:
                name_neigh[name] = set()
            if last_name:
                name_neigh[last_name].add(name)
            last_name = name
    return name_neigh


def print_graph(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)
    servers = np.unique(pd.read_csv(in_path)["server"].values)
    for server in servers:
        name_neigh = get_graph(dt_start, dt_end, server)

        utils.create_dirs(["{}/prints/{}/filtered/graph/".format(script_dir,
                                                                 str_dt),
                           "{}/prints/{}/filtered/graph/{}".format(script_dir,
                                                                   str_dt,
                                                                   server)])
        out_path = "{}/prints/{}/filtered/graph/{}/graph.gv".format(script_dir,
                                                                    str_dt,
                                                                    server)
        with open(out_path, "w") as f:
            f.write("digraph {\n")
            for name in name_neigh:
                for neigh in name_neigh[name]:
                    f.write("   \"{}\" -> \"{}\"\n".format(name, neigh))
            f.write("}")


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 7, 21)
    dt_end = datetime.datetime(2016, 7, 31)
    print_graph(dt_start, dt_end)
