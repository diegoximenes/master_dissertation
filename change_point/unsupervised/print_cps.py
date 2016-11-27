import os
import sys
import datetime
import functools
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.read_input as read_input
from utils.time_series import TimeSeries
import change_point.utils.cp_utils as cp_utils


def update_type_cps(type_cps, mean1, mean2):
    if np.isclose(mean1, mean2):
        type_cps.append("same")
    elif mean1 > mean2:
        type_cps.append("decrease")
    else:
        type_cps.append("increase")


def create_csv_with_same_header(out_path, df):
    with open(out_path, "w") as f:
        l_period = ",{}" * (len(df.columns.values) - 1)
        l_formatter = "{}" + l_period + "\n"
        f.write(l_formatter.format(*df.columns.values))


def print_cps_per_path(dt_start, dt_end, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots".format(script_dir),
                       "{}/plots/paths".format(script_dir),
                       "{}/plots/paths/{}".format(script_dir, str_dt),
                       "{}/plots/paths/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)

    path_dirs = set()

    in_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                str_dt, metric)
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac = row["mac"]
        server = row["server"]
        traceroute = mac_traceroute[mac]

        dir_path = "{}/plots/paths/{}/{}/{}/".format(script_dir, str_dt,
                                                     metric, server)
        utils.create_dirs([dir_path])

        first_hop = True
        for name in reversed(traceroute):
            if (name[0][0] is None) and first_hop:
                continue
            splitted = name[0][0].split(".")
            if splitted[0] == "192":
                continue
            first_hop = False

            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/cps_per_mac.csv".format(dir_path)
            if dir_path not in path_dirs:
                create_csv_with_same_header(out_path, df)
            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)
            path_dirs.add(dir_path)


def print_cps_per_name(dt_start, dt_end, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots".format(script_dir),
                       "{}/plots/names/".format(script_dir),
                       "{}/plots/names/{}".format(script_dir, str_dt),
                       "{}/plots/names/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)

    name_dirs = set()

    in_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                str_dt, metric)
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac = row["mac"]
        server = row["server"]
        traceroute = mac_traceroute[mac]

        dir_path = "{}/plots/names/{}/{}/{}/".format(script_dir, str_dt,
                                                     metric, server)
        utils.create_dirs([dir_path])

        for name in cp_utils.iter_names_traceroute_filtered(traceroute):
            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/cps_per_mac.csv".format(dir_path)
            if dir_path not in name_dirs:
                create_csv_with_same_header(out_path, df)
            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)
            name_dirs.add(dir_path)


def print_cps(dt_start, dt_end, dir_model, metric, filtered):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/prints/".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt),
                       "{}/prints/{}/{}".format(script_dir, str_dt, filtered),
                       "{}/prints/{}/{}/{}".format(script_dir, str_dt,
                                                   filtered, metric)])

    out_path = "{}/prints/{}/{}/{}/cps_per_mac.csv".format(script_dir, str_dt,
                                                           filtered, metric)
    with open(out_path, "w") as f:
        f.write("server,mac,cp_dt,type_cps,seg_means\n")
        in_path_dir = ("{}/change_point/models/{}/plots/unsupervised/{}/{}".
                       format(base_dir, dir_model, str_dt, metric))

        target_macs = read_input.get_macs_traceroute_filter(dt_start, dt_end,
                                                            filtered)

        cnt = 0
        for file_name in os.listdir(in_path_dir):
            if ".csv" in file_name:
                cnt += 1
                print "cnt={}".format(cnt)

                server = file_name.split("server")[1].split("_")[0]
                mac = file_name.split("mac")[1].split("_")[0]

                if mac not in target_macs:
                    continue

                dt_cps = []
                id_cps = []
                df = pd.read_csv("{}/{}".format(in_path_dir, file_name))
                for idx, row in df.iterrows():
                    dt_cps.append(row["dt"])
                    id_cps.append(row["dt_id"])

                in_path = utils.get_in_path(server, mac, dt_start, dt_end)
                ts = TimeSeries(in_path, metric, dt_start, dt_end)

                seg_means = []
                type_cps = []
                if id_cps:
                    mean1 = np.mean(ts.y[0:id_cps[0]])
                    seg_means.append(mean1)
                    for i in range(1, len(id_cps)):
                        mean2 = np.mean(ts.y[id_cps[i - 1]:id_cps[i]])
                        seg_means.append(mean2)
                        update_type_cps(type_cps, mean1, mean2)
                        mean1 = mean2
                    mean2 = np.mean(ts.y[id_cps[-1]:-1])
                    seg_means.append(mean2)
                    update_type_cps(type_cps, mean1, mean2)

                f.write("{},{},\"{}\",\"{}\",\"{}\"\n".format(server, mac,
                                                              dt_cps, type_cps,
                                                              seg_means))


def run_parallel(dir_model, metric, filtered, hours_tol):
    dt_ranges = list(utils.iter_dt_range())
    fp_print_cps = functools.partial(print_cps,
                                     dir_model=dir_model,
                                     metric=metric,
                                     filtered=filtered)
    utils.parallel_exec(fp_print_cps, dt_ranges)

    fp_print_cps_per_name = \
        functools.partial(print_cps_per_name, metric=metric)
    utils.parallel_exec(fp_print_cps_per_name, dt_ranges)

    fp_print_cps_per_path = \
        functools.partial(print_cps_per_path, metric=metric)
    utils.parallel_exec(fp_print_cps_per_path, dt_ranges)


def run_sequential(dir_model, metric, filtered, hours_tol):
    for dt_start, dt_end in utils.iter_dt_range():
        print_cps(dt_start, dt_end, dir_model, metric, filtered)
        print_cps_per_name(dt_start, dt_end, metric)
        print_cps_per_path(dt_start, dt_end, metric)


def run_single(dir_model, metric, filtered, hours_tol, dt_start, dt_end):
    print_cps(dt_start, dt_end, dir_model, metric, filtered)
    print_cps_per_name(dt_start, dt_end, metric)
    print_cps_per_path(dt_start, dt_end, metric)


if __name__ == "__main__":
    metric = "latency"
    dir_model = "seg_neigh"
    hours_tol = 4
    filtered = "filtered"

    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(dir_model, metric, filtered, hours_tol, dt_start, dt_end)
    # run_parallel(dir_model, metric, filtered, hours_tol)
    # run_sequential(dir_model, metric, filtered, hours_tol)
