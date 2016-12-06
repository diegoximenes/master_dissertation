import os
import sys
import datetime
import ast
import shutil
import functools
import pandas as pd
import numpy as np
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.dt_procedures as dt_procedures
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


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
            u = line.split(" -> ")[0].lstrip(" ").lstrip("\"").rstrip("\"")
            v = line.split(" -> ")[1].rstrip("\n").lstrip("\"").rstrip("\"")
            g[u].append(v)
    return g


def all_clients_with_same_pattern(name, cp_dt, str_dt, metric, server,
                                  hour_tol=4):
    in_path = "{}/plots/names/{}/{}/{}/{}/cps_per_mac.csv".format(script_dir,
                                                                  str_dt,
                                                                  metric,
                                                                  server,
                                                                  name)

    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        match_row = False
        for strdt in ast.literal_eval(row["cp_dt"]):
            dt = dt_procedures.from_strdt_to_dt(strdt)
            if dt_procedures.dt_is_close(dt, cp_dt, hour_tol):
                match_row = True
        if not match_row:
            return False
    return True


def analyse_path(path, cp_dt_start, cp_dt_end, str_dt, metric,
                 server):
    cp_dt = cp_dt_start + (cp_dt_end - cp_dt_start) / 2
    for i, name in enumerate(path[1:]):
        if not all_clients_with_same_pattern(name, cp_dt, str_dt, metric,
                                             server):
                return path[0:i + 1]
    return path


def analyse_zero_in_deg_vertex(g, u, metric, server, dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    path = [u]
    while (u in g) and (len(g[u]) != 0):
        u = g[u][0]
        path.append(u)

    dir_path = "/".join(list(reversed(path)))
    dir_path = "{}/plots/paths/{}/{}/{}/{}".format(script_dir, str_dt, metric,
                                                   server, dir_path)

    out_path = "{}/problem_location.csv".format(dir_path)
    with open(out_path, "w") as f:
        f.write("cp_dt_start,cp_dt_end,cp_type,fraction_of_clients,"
                "cnt_clients,clients,problem_location\n")
        in_path = "{}/match_cps.csv".format(dir_path)
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            if np.isclose(row["fraction_of_clients"], 1.0):
                cp_dt_start = dt_procedures.from_strdt_to_dt(
                    row["cp_dt_start"])
                cp_dt_end = dt_procedures.from_strdt_to_dt(row["cp_dt_end"])
                problem_location = analyse_path(path, cp_dt_start,
                                                cp_dt_end, str_dt, metric,
                                                server)
                problem_location = map(ast.literal_eval, problem_location)
            else:
                problem_location = ["before"]
            l_format = "{},{},{},{},{},\"{}\",\"{}\"\n"
            f.write(l_format.format(row["cp_dt_start"], row["cp_dt_end"],
                                    row["cp_type"],
                                    row["fraction_of_clients"],
                                    row["cnt_clients"],
                                    row["clients"], problem_location))

    out_path_name = "{}/plots/names/{}/{}/{}/{}".format(script_dir, str_dt,
                                                        metric, server,
                                                        path[0])
    shutil.copy(out_path, out_path_name)


def suffix_match(ll):
    suffix = []
    initial_len_ll = len(ll)
    while len(ll) == initial_len_ll:
        last = ll[0][-1]
        ll_aux = []
        for l in ll:
            if last != l[-1]:
                return suffix
            if l[:-1]:
                ll_aux.append(l[:-1])
        ll = ll_aux
        suffix.append(last)
    return suffix


def correlation_zero_in_deg_vertexes(g, mac_degin, server, dt_start, dt_end,
                                     metric, eps_hours):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/plots/paths/{}/{}/{}/problem_correlation.csv".
                format(script_dir, str_dt, metric, server))
    with open(out_path, "w") as f:
        f.write("cp_dt_start,cp_dt_end,cp_type,"
                "cnt_vertexes_with_zero_in_deg,suffix_match,"
                "vertexes_with_zero_in_deg\n")
        for u in g:
            l = []
            if mac_degin[u] == 0:
                in_path = ("{}/plots/names/{}/{}/{}/{}/"
                           "problem_location.csv".format(script_dir,
                                                         str_dt,
                                                         metric,
                                                         server, u))
                df = pd.read_csv(in_path)

                for cp_type in cp_utils.iter_cp_types():
                    for idx, row in df[df["cp_type"] == cp_type].iterrows():
                        cp_dt_start = dt_procedures.from_strdt_to_dt(
                            row["cp_dt_start"])
                        cp_dt_end = dt_procedures.from_strdt_to_dt(
                            row["cp_dt_end"])
                        cp_dt = cp_dt_start + (cp_dt_end - cp_dt_start) / 2

                        problem_locations = ast.literal_eval(
                            row["problem_location"])

                        dic = {"dt": cp_dt, "name": ast.literal_eval(u),
                               "problem_locations": problem_locations,
                               "fraction_of_clients":
                               row["fraction_of_clients"],
                               "cnt_clients": row["cnt_clients"]}

                        if problem_locations == ["before"]:
                            dic["dt"] = str(dic["dt"])
                            f.write("{},{},{},\"{}\",\"{}\"\n".
                                    format(row["cp_dt_start"],
                                           row["cp_dt_end"],
                                           cp_type,
                                           1,
                                           problem_locations,
                                           [dic]))
                        else:
                            l.append(dic)

                    votes = \
                        unsupervised_utils.multiple_inexact_voting(l,
                                                                   eps_hours)
                    for vote in votes:
                        suffix_matches = suffix_match(
                            map(lambda dic: dic["problem_locations"],
                                vote["interval"]))
                        if suffix_matches == []:
                            suffix_matches = ["empty"]

                        for dic in vote["interval"]:
                            dic["dt"] = str(dic["dt"])
                        f.write("{},{},{},{},\"{}\",\"{}\"\n".
                                format(vote["l_dt"],
                                       vote["r_dt"],
                                       cp_type,
                                       len(vote["interval"]),
                                       suffix_matches,
                                       vote["interval"]))

    out_path_name = ("{}/plots/names/{}/{}/{}".
                     format(script_dir, str_dt, metric,
                            server))
    shutil.copy(out_path, out_path_name)


def aggregate_server_correlations(dt_start, dt_end, metric, servers):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/filtered/{}/problem_correlation.csv".
                format(script_dir, str_dt, metric))
    with open(out_path, "w") as f:
        f.write("server,cp_dt_start,cp_dt_end,cp_type,"
                "cnt_vertexes_with_zero_in_deg,suffix_match,"
                "vertexes_with_zero_in_deg\n")
        for server in servers:
            if not valid_graph(dt_start, dt_end, server):
                continue
            in_path = ("{}/plots/names/{}/{}/{}/problem_correlation.csv".
                       format(script_dir, str_dt, metric, server))
            df = pd.read_csv(in_path)
            for idx, row in df.iterrows():
                f.write("{},{},{},{},\"{}\",\"{}\"\n".
                        format(server,
                               row["cp_dt_start"],
                               row["cp_dt_end"],
                               row["cnt_vertexes_with_zero_in_deg"],
                               row["suffix_match"],
                               row["vertexes_with_zero_in_deg"]))
    utils.sort_csv_file(out_path, ["cnt_vertexes_with_zero_in_deg"],
                        ascending=False)


def localize_problems(dt_start, dt_end, metric, eps_hours):
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

            for u in g:
                if mac_degin[u] == 0:
                    analyse_zero_in_deg_vertex(g, u, metric, server, dt_start,
                                               dt_end)

            correlation_zero_in_deg_vertexes(g, mac_degin, server, dt_start,
                                             dt_end, metric, eps_hours)

    aggregate_server_correlations(dt_start, dt_end, metric, servers)


def run_sequential(metric, eps_hours):
    for dt_start, dt_end in utils.iter_dt_range():
        localize_problems(dt_start, dt_end, metric, eps_hours)


def run_parallel(metric, eps_hours):
    dt_ranges = list(utils.iter_dt_range())
    f_localize_problems = functools.partial(localize_problems, metric=metric,
                                            eps_hours=eps_hours)
    utils.parallel_exec(f_localize_problems, dt_ranges)


def run_single(dt_start, dt_end, metric, eps_hours):
    localize_problems(dt_start, dt_end, metric, eps_hours)


if __name__ == "__main__":
    eps_hours = 4
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    parallel_args = {"eps_hours": eps_hours, "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start,
                   "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args)
