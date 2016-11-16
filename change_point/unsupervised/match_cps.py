import os
import sys
import ast
import datetime
import functools
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.read_input as read_input
import change_point.utils.cmp_class as cmp_class
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def match_cps(dt_start, dt_end, metric, hours_tol, filtered):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/{}/{}/cps_per_mac.csv".format(script_dir, str_dt,
                                                          filtered, metric)

    mac_cps = {}
    mac_server = {}
    mac_typeCps = {}
    mac_segMeans = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        str_dts = ast.literal_eval(row["cp_dt"])
        dts = []
        for strdt in str_dts:
            dts.append(dt_procedures.from_strdt_to_dt(strdt))
        mac_cps[row["mac"]] = dts
        mac_server[row["mac"]] = row["server"]
        mac_typeCps[row["mac"]] = row["type_cps"]
        mac_segMeans[row["mac"]] = row["seg_means"]

    out_path = "{}/prints/{}/{}/{}/match_cps.csv".format(script_dir, str_dt,
                                                         filtered, metric)
    with open(out_path, "w") as f:
        f.write("server1,server2,mac1,mac2,tp,fp,fn,cp_dt1,cp_dt2,type_cps1,"
                "type_cps2,seg_means1,seg_means2\n")

        cnt = 0
        for mac1 in mac_cps:
            cnt += 1
            print "cnt={}".format(cnt)

            for mac2 in mac_cps:
                if mac1 != mac2:
                    str_cps1 = map(str, mac_cps[mac1])
                    str_cps2 = map(str, mac_cps[mac2])

                    # only tp, fp, fn are correct with this parameters
                    ts = TimeSeries()
                    conf = cmp_class.conf_mat(mac_cps[mac1], mac_cps[mac2], ts,
                                              dt_procedures.dt_is_close,
                                              hours_tol)
                    formatter = "{}" + ",{}" * 6 + ",\"{}\"" * 6 + "\n"
                    f.write(formatter.format(mac_server[mac1],
                                             mac_server[mac2],
                                             mac1,
                                             mac2,
                                             conf["tp"],
                                             conf["fp"],
                                             conf["fn"],
                                             str_cps1,
                                             str_cps2,
                                             mac_typeCps[mac1],
                                             mac_typeCps[mac2],
                                             mac_segMeans[mac1],
                                             mac_segMeans[mac2]))

    utils.sort_csv_file(out_path, ["tp", "fp", "fn"],
                        ascending=[False, True, True])


def update_type_cps(type_cps, mean1, mean2):
    if np.isclose(mean1, mean2):
        type_cps.append("same")
    elif mean1 > mean2:
        type_cps.append("decrease")
    else:
        type_cps.append("increase")


def print_cps_per_mac(dt_start, dt_end, dir_model, metric, filtered):
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
    fp_print_cps_per_mac = functools.partial(print_cps_per_mac,
                                             dir_model=dir_model,
                                             metric=metric,
                                             filtered=filtered)
    utils.parallel_exec(fp_print_cps_per_mac, dt_ranges)
    fp_match_cps = functools.partial(match_cps,
                                     metric=metric,
                                     hours_tol=hours_tol,
                                     filtered=filtered)
    utils.parallel_exec(fp_match_cps, dt_ranges)


def run_sequential(dir_model, metric, filtered, hours_tol):
    for dt_start, dt_end in utils.iter_dt_range():
        print_cps_per_mac(dt_start, dt_end, dir_model, metric, filtered)
        match_cps(dt_start, dt_end, metric, hours_tol, filtered)


def run_single(dir_model, metric, filtered, hours_tol, dt_start, dt_end):
    print_cps_per_mac(dt_start, dt_end, dir_model, metric, filtered)
    match_cps(dt_start, dt_end, metric, hours_tol, filtered)


if __name__ == "__main__":
    metric = "latency"
    dir_model = "seg_neigh"
    hours_tol = 4
    filtered = "filtered"

    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(dir_model, metric, filtered, hours_tol, dt_start, dt_end)
    # run_parallel(dir_model, metric, filtered, hours_tol)
    # run_sequential(dir_model, metric, filtered, hours_tol)
