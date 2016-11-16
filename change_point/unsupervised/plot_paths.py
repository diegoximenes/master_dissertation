import sys
import os
import datetime
import ast
import functools
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def plot_per_path(dt_start, dt_end, metric, plot_cps=False):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/paths".format(script_dir),
                       "{}/plots/paths/{}".format(script_dir, str_dt),
                       "{}/plots/paths/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    mac_cps = {}
    if plot_cps:
        in_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                    str_dt,
                                                                    metric)
        if os.path.isfile(in_path):
            df = pd.read_csv(in_path)
            for idx, row in df.iterrows():
                mac_cps[row["mac"]] = map(dt_procedures.from_strdt_to_dt,
                                          ast.literal_eval(row["cp_dt"]))

    df = pd.read_csv("{}/prints/{}/filtered/traceroute_per_mac.csv".
                     format(script_dir, str_dt))
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}, str_dt={}".format(cnt, str_dt)

        utils.create_dirs(["{}/plots/paths/{}/{}/{}".format(script_dir, str_dt,
                                                            metric,
                                                            row["server"])])

        traceroute = ast.literal_eval(row["traceroute_filtered"])

        in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir,
                                                 row["server"], row["mac"])
        out_file_name = utils.get_out_file_name(row["server"], row["mac"],
                                                dt_start, dt_end)

        ts = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter.percentile_filter(win_len=13, p=0.5)

        first_hop = True
        dir_path = "{}/plots/paths/{}/{}/{}/".format(script_dir, str_dt,
                                                     metric, row["server"])
        for name in traceroute:
            if (name[0][0] is None) and first_hop:
                continue
            splitted = name[0][0].split(".")
            if splitted[0] == "192":
                continue

            cp_dts = {}
            if plot_cps:
                if row["mac"] in mac_cps:
                    cp_dts = mac_cps[row["mac"]]

            first_hop = False
            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/{}.png".format(dir_path, out_file_name)

            plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
                                            compress=False,
                                            plot_type2="scatter",
                                            dt_axvline1=cp_dts,
                                            dt_axvline2=cp_dts)


def run_parallel(metric):
    dt_ranges = list(utils.iter_dt_range())
    f_plot_per_path = functools.partial(plot_per_path, metric=metric)
    utils.parallel_exec(f_plot_per_path, dt_ranges)


def run_sequential(metric):
    for dt_start, dt_end in utils.iter_dt_range():
        plot_per_path(dt_start, dt_end, metric)


def run_single(metric, dt_start, dt_end):
    plot_per_path(dt_start, dt_end, metric, True)


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(metric, dt_start, dt_end)
    # run_parallel(metric)
    # run_sequential(metric)
