import os
import sys
import datetime
import functools
import pandas as pd
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.utils.cp_utils as cp_utils


def match_cps_per_path(dt_start, dt_end, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)

    write_dir = set()

    in_path = "{}/prints/{}/filtered/{}/match_cps.csv".format(script_dir,
                                                              str_dt, metric)
    df = pd.read_csv(in_path)
    for cnt, (idx, row) in enumerate(df.iterrows()):
        print "cnt={}/{}".format(cnt, df.shape[0])

        if row["server1"] != row["server2"]:
            continue

        server = row["server1"]
        mac1 = row["mac1"]
        mac2 = row["mac2"]

        if (mac1 not in mac_traceroute) or (mac2 not in mac_traceroute):
            continue

        dir_path = "{}/plots/paths/{}/{}/{}/".format(script_dir, str_dt,
                                                     metric, server)
        first_hop = True
        for name1, name2 in izip(mac_traceroute[mac1], mac_traceroute[mac2]):
            if (name1[0][0] is None) and (name2[0][0] is None) and first_hop:
                continue
            if (name1[0][0] is not None) and (name2[0][0] is not None):
                splitted1 = name1[0][0].split(".")
                splitted2 = name2[0][0].split(".")
                if (splitted1[0] == "192") and (splitted2[0] == "192"):
                    continue

            if name1 != name2:
                break

            first_hop = False
            dir_path = "{}/{}".format(dir_path, name1)
            utils.create_dirs([dir_path])
            out_path = "{}/matches_cps.csv".format(dir_path)

            if dir_path not in write_dir:
                with open(out_path, "w") as f:
                    l_period = ",{}" * (len(df.columns.values) - 1)
                    l_formatter = "{}" + l_period + "\n"
                    f.write(l_formatter.format(*df.columns.values))

            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)

            write_dir.add(dir_path)


def run_sequential(metric):
    for dt_start, dt_end in utils.iter_dt_range():
        match_cps_per_path(dt_start, dt_end, metric)


def run_parallel(metric):
    dt_ranges = list(utils.iter_dt_range())
    f_match_cps_per_path = functools.partial(match_cps_per_path, metric=metric)
    utils.parallel_exec(f_match_cps_per_path, dt_ranges)


def run_single(metric, dt_start, dt_end):
    match_cps_per_path(dt_start, dt_end, metric)

if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(metric, dt_start, dt_end)
    # run_parallel(metric)
    # run_sequential(metric)
