import os
import sys
import datetime
import functools
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.utils.cp_utils as cp_utils


def match_cps_per_name(metric, dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/names/".format(script_dir),
                       "{}/plots/names/{}/".format(script_dir, str_dt),
                       "{}/plots/names/{}/{}/".format(script_dir, str_dt,
                                                      metric)])

    in_path = "{}/prints/{}/filtered/{}/match_cps.csv".format(script_dir,
                                                              str_dt, metric)

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)
    name_dir = set()
    df = pd.read_csv(in_path)
    for cnt, (idx, row) in enumerate(df.iterrows()):
        print "cnt={}/{}".format(cnt, df.shape[0])

        names1 = set(cp_utils.iter_names_traceroute_filtered(
            mac_traceroute[row["mac1"]]))
        names2 = set(cp_utils.iter_names_traceroute_filtered(
            mac_traceroute[row["mac2"]]))
        names_intersection = names1.intersection(names2)

        for name in names_intersection:
            dir_path = "{}/plots/names/{}/{}/{}".format(script_dir, str_dt,
                                                        metric, name)
            out_path = ("{}/match_cps.csv".format(dir_path))
            utils.create_dirs([dir_path])

            if name not in name_dir:
                with open(out_path, "w") as f:
                    l_period = ",{}" * (len(df.columns.values) - 1)
                    l_formatter = "{}" + l_period + "\n"
                    f.write(l_formatter.format(*df.columns.values))

            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)

            name_dir.add(name)


def run_single(metric, dt_start, dt_end):
    match_cps_per_name(metric, dt_start, dt_end)


def run_parallel(metric):
    dt_ranges = list(utils.iter_dt_range())
    fp_match_cps_per_name = functools.partial(match_cps_per_name,
                                              metric=metric)
    utils.parallel_exec(fp_match_cps_per_name, dt_ranges)


def run_sequential(metric):
    for dt_start, dt_end in utils.iter_dt_range():
        match_cps_per_name(dt_start, dt_end, metric)


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(metric, dt_start, dt_end)
    # run_parallel(metric)
    # run_sequential(metric)
