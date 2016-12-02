import os
import sys
import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def get_deg_in(g):
    u_degin = defaultdict(int)
    for u in g:
        for v in g[u]:
            u_degin[v] += 1
    return u_degin


def valid_graph(dt_start, dt_end, server):
    str_dt = utils.get_str_dt(dt_start, dt_end)
    in_path = ("{}/prints/{}/filtered/graph/{}/graph_stats.txt".
               format(script_dir, str_dt, server))
    with open(in_path) as f:
        for line in f:
            if "valid_graph=" in line:
                return (line.split("=")[-1].rstrip("\n") == "True")


def read_graph(dt_start, dt_end, server):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    g = defaultdict(list)
    in_path = "{}/prints/{}/filtered/graph/{}/graph.gv".format(script_dir,
                                                               str_dt, server)
    with open(in_path) as f:
        for line in f.readlines()[1:-1]:
            u = line.split(" -> ")[0].lstrip(" ")
            v = line.split(" -> ")[1]
            g[u].append(v)
    return g


def all_clients_with_problem_in_name(metric, dt_start, dt_end, server, name):
    str_dt = utils.get_str_dt(dt_start, dt_end)
    in_path = "{}/plots/names/{}/{}/{}/match_cps.csv".format(script_dir,
                                                             str_dt, server,
                                                             name)

    return False


def analyse_path(g, u, metric, dt_start, dt_end, server):
    path = [u]
    while len(g[u]) != 0:
        u = g[u][0]
        path.append(u)

    for i, u in enumerate(path):
        if all_clients_with_problem_in_name(metric, dt_start, dt_end, server,
                                            u):
            return path[0:i]

    return path


def localize_problems(dt_start, dt_end, metric):
    """
    considers that the graph is a tree
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)
    servers = np.unique(pd.read_csv(in_path)["server"].values)
    for server in servers:
        if valid_graph(dt_start, dt_end, server):
            g = read_graph(dt_start, dt_end, server)
            mac_degin = get_deg_in(g)

            cp_dts = get_cp_dts(metric, dt_start, dt_end, server)

            for u in g:
                if mac_degin[u] == 0:
                    possible_problems = analyse_path(g, u, metric, dt_start,
                                                     dt_end, server)
                    print possible_problems
                    return


def run_single(dt_start, dt_end):
    localize_problems(dt_start, dt_end)


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(dt_start, dt_end, metric)
    # run_parallel()
    # run_sequential()
