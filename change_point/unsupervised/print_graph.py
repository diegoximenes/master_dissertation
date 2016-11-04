import os
import sys
import ast
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def print_graph(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)

    name_neigh = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        traceroute = ast.literal_eval(row["traceroute_filtered"])
        last_name = None
        for name in traceroute:
            if name not in name_neigh:
                name_neigh[name] = set()

            if last_name:
                name_neigh[last_name].add(name)
            last_name = name

    out_path = "{}/prints/{}/filtered/graph.txt".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        for name in name_neigh:
            f.write("{}: ".format(name))
            for neigh in name_neigh[name]:
                f.write("{},".format(neigh))
            f.write("\n")


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)
    print_graph(dt_start, dt_end)
