import os
import sys
import ast
import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


def get_graph(dt_start, dt_end, valid_traceroute_field, traceroute_field,
              server=None):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)

    names = set()
    name_neigh = {}
    df = pd.read_csv(in_path)
    if server:
        df = df[df["server"] == server]
    for idx, row in df.iterrows():
        if row["valid_cnt_samples"] and row[valid_traceroute_field]:
            traceroute = ast.literal_eval(row[traceroute_field])
            last_name = None
            for name in traceroute:
                names.add(name)
                if name not in name_neigh:
                    name_neigh[name] = set()
                if last_name:
                    name_neigh[last_name].add(name)
                last_name = name

    for name in names:
        if name not in name_neigh:
            name_neigh[name] = set()

    return name_neigh


def write_graph(out_path, name_neigh):
    with open(out_path, "w") as f:
        f.write("digraph {\n")
        for name in name_neigh:
            for neigh in name_neigh[name]:
                f.write("   \"{}\" -> \"{}\"\n".format(name, neigh))
        f.write("}")


def check_graph(out_dir, name_neigh, traceroute_field):
    def dfs(name_neigh, mark, name, f=None):
        mark[name] = 1

        if f:
            for neigh in name_neigh[name]:
                f.write("  \"{}\" -> \"{}\"\n".format(name, neigh))

        for neigh in name_neigh[name]:
            if mark[neigh]:
                return False
            else:
                dfs_ret = dfs(name_neigh, mark, neigh, f)
                if not dfs_ret:
                    return dfs_ret
        return True

    in_deg = defaultdict(int)
    out_deg = defaultdict(int)
    for name in name_neigh:
        for neigh in name_neigh[name]:
            in_deg[neigh] += 1
            out_deg[name] += 1

    valid_graph = True
    for name in name_neigh:
        if in_deg[name] == 0:
            mark = defaultdict(int)
            if not dfs(name_neigh, mark, name):
                valid_graph = False
                mark = defaultdict(int)
                out_path = "{}/{}_invalid_subgraph.gv".format(out_dir,
                                                              traceroute_field)
                f = open(out_path, "w")
                f.write("digraph {\n")
                dfs(name_neigh, mark, name, f)
                f.write("}")
                f.close()
                break

    # empty graph
    if not name_neigh:
        valid_graph = False

    out_path = "{}/{}_graph_stats.txt".format(out_dir, traceroute_field)
    with open(out_path, "w") as f:
        f.write("valid_graph={}\n".format(valid_graph))


def process_graphs(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_dir = "{}/prints/{}/filtered/graph/".format(script_dir, str_dt)
    utils.create_dirs([out_dir])

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)
    servers = np.unique(pd.read_csv(in_path)["server"].values)

    for traceroute_type in unsupervised_utils.iter_traceroute_types():
        valid_traceroute_field, traceroute_field = \
            cp_utils.get_traceroute_fields(traceroute_type)

        for server in servers:
            utils.create_dirs(["{}/prints/{}/filtered/graph/".
                               format(script_dir, str_dt),
                               "{}/prints/{}/filtered/graph/{}".
                               format(script_dir, str_dt, server)])

            out_dir = "{}/prints/{}/filtered/graph/{}".format(script_dir,
                                                              str_dt,
                                                              server)
            out_path = "{}/{}_graph.gv".format(out_dir, traceroute_field)

            name_neigh = get_graph(dt_start, dt_end, valid_traceroute_field,
                                   traceroute_field, server)
            write_graph(out_path, name_neigh)
            check_graph(out_dir, name_neigh, traceroute_field)


def run_parallel():
    dt_ranges = list(utils.iter_dt_range())
    utils.parallel_exec(process_graphs, dt_ranges)


def run_sequential():
    for dt_start, dt_end in utils.iter_dt_range():
        process_graphs(dt_start, dt_end)


def run_single(dt_start, dt_end):
    process_graphs(dt_start, dt_end)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
