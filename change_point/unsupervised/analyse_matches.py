import os
import sys
import datetime
import functools
import pandas as pd
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def analyse_matches(dir_path):
    def dfs(u, cc):
        mark[u] = cc
        for v in g[u]:
            if mark[v] == 0:
                dfs(v, cc)

    def is_clique(cc):
        cc = list(cc)
        for i in xrange(len(cc)):
            for j in xrange(i + 1, len(cc)):
                for k in xrange(j + 1, len(cc)):
                    u = cc[i]
                    v = cc[j]
                    w = cc[k]
                    if (v not in g[u]) or (w not in g[u]) or (w not in g[v]):
                        return False
        return True

    in_path = "{}/match_cps.csv".format(dir_path)
    out_path = "{}/cps_cc.csv".format(dir_path)

    g = {}
    mark = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        if row["mac1"] not in g:
            g[row["mac1"]] = []
            mark[row["mac1"]] = 0
        if row["mac2"] not in g:
            g[row["mac2"]] = []
            mark[row["mac2"]] = 0

        if (row["tp"] > 0) and (row["fp"] == 0) and (row["fn"] == 0):
            g[row["mac1"]].append(row["mac2"])
            g[row["mac2"]].append(row["mac1"])

    cc = 1
    for u in g:
        if mark[u] == 0:
            dfs(u, cc)
            cc += 1
    ccs = defaultdict(set)
    for u in g:
        ccs[mark[u]].add(u)

    with open(out_path, "w") as f:
        f.write("cc,macs,is_clique\n")
        for cc in ccs:
            f.write("{},\"{}\",{}\n".format(cc, list(ccs[cc]),
                                            is_clique(ccs[cc])))


def dirs_match_all(str_dt, metric):
    return ["{}/prints/{}/filtered/{}".format(script_dir, str_dt, metric)]


def dirs_match_per_name(str_dt, metric):
    in_dir = "{}/plots/names/{}/{}/".format(script_dir, str_dt, metric)
    for name in os.listdir(in_dir):
        yield "{}/{}".format(in_dir, name)


def dirs_match_per_path(str_dt, metric):
    in_dir = "{}/plots/paths/{}/{}".format(script_dir, str_dt, metric)
    for dir_path, _, file_names in os.walk(in_dir):
        if "match_cps.csv" in file_names:
            yield dir_path


def run_single(dt_start, dt_end, f_dirs, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)
    for dir_path in f_dirs(str_dt, metric):
        analyse_matches(dir_path)


def run_sequential(f_dirs, metric):
    for dt_start, dt_end in utils.iter_dt_range():
        run_single(dt_start, dt_end, f_dirs, metric)


def run_parallel(f_dirs, metric):
    dt_ranges = list(utils.iter_dt_range())
    fp = functools.partial(run_single, f_dirs=f_dirs, metric=metric)
    utils.parallel_exec(fp, dt_ranges)


if __name__ == "__main__":
    f_dirs = dirs_match_per_path
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(dt_start, dt_end, f_dirs, metric)
    # run_parallel(f_dirs, metric)
    # run_sequential(f_dirs, metric)
