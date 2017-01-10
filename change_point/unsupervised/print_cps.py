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
from utils.time_series import TimeSeries
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
import change_point.cp_utils.cp_utils as cp_utils


def update_type_cps(type_cps, mean1, mean2, metric):
    if np.isclose(mean1, mean2):
        type_cps.append("inconclusive")
    if "throughput" in metric:
        if mean1 > mean2:
            type_cps.append("failure")
        else:
            type_cps.append("improvement")
    else:
        if mean1 > mean2:
            type_cps.append("improvement")
        else:
            type_cps.append("failure")


def print_cps(dt_start, dt_end, dir_model, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/prints/".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt),
                       "{}/prints/{}/filtered".format(script_dir, str_dt),
                       "{}/prints/{}/filtered/{}".format(script_dir, str_dt,
                                                         metric)])

    out_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                 str_dt,
                                                                 metric)
    with open(out_path, "w") as f:
        f.write("server,mac,cp_dts,type_cps,seg_means\n")
        in_path_dir = ("{}/change_point/models/{}/plots/unsupervised/{}/{}".
                       format(base_dir, dir_model, str_dt, metric))

        cnt = 0
        for file_name in os.listdir(in_path_dir):
            if ".csv" in file_name:
                cnt += 1
                print "cnt={}".format(cnt)

                server = file_name.split("server")[1].split("_")[0]
                mac = file_name.split("mac")[1].split("_")[0]

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
                        update_type_cps(type_cps, mean1, mean2, metric)
                        mean1 = mean2
                    mean2 = np.mean(ts.y[id_cps[-1]:-1])
                    seg_means.append(mean2)
                    update_type_cps(type_cps, mean1, mean2, metric)

                f.write("{},{},\"{}\",\"{}\",\"{}\"\n".format(server, mac,
                                                              dt_cps, type_cps,
                                                              seg_means))


def run_parallel(dir_model, metric):
    dt_ranges = list(utils.iter_dt_range())
    fp_print_cps = functools.partial(print_cps,
                                     dir_model=dir_model,
                                     metric=metric)
    utils.parallel_exec(fp_print_cps, dt_ranges)

    fp_print_per_name = functools.partial(unsupervised_utils.print_per_name,
                                          metric=metric,
                                          file_name="cps_per_mac.csv")
    utils.parallel_exec(fp_print_per_name, dt_ranges)

    fp_print_per_path = functools.partial(unsupervised_utils.print_per_path,
                                          metric=metric,
                                          file_name="cps_per_mac.csv")
    utils.parallel_exec(fp_print_per_path, dt_ranges)


def run_sequential(dir_model, metric):
    for dt_start, dt_end in utils.iter_dt_range():
        print_cps(dt_start, dt_end, dir_model, metric)
        unsupervised_utils.print_cps_per_name(dt_start, dt_end, metric,
                                              "cps_per_mac.csv")
        unsupervised_utils.print_cps_per_path(dt_start, dt_end, metric,
                                              "cps_per_mac.csv")


def run_single(dir_model, metric, dt_start, dt_end):
    print_cps(dt_start, dt_end, dir_model, metric)
    unsupervised_utils.print_per_name(dt_start, dt_end, metric,
                                      "cps_per_mac.csv")
    unsupervised_utils.print_per_path(dt_start, dt_end, metric,
                                      "cps_per_mac.csv")


if __name__ == "__main__":
    metric = "latency"
    dir_model = "seg_neigh"
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {"dir_model": dir_model, "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
