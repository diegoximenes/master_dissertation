import sys
import os
import datetime
import ast
import functools
import shutil
import pandas as pd
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


def plot_per_path(dt_start, dt_end, metric, plot_cps=False):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/paths".format(script_dir),
                       "{}/plots/paths/{}".format(script_dir, str_dt),
                       "{}/plots/paths/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    # get client->cps mapping
    client_cps = defaultdict(list)
    if plot_cps:
        in_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                    str_dt,
                                                                    metric)
        if os.path.isfile(in_path):
            df = pd.read_csv(in_path)
            for idx, row in df.iterrows():
                client_cps[(row["server"], row["mac"])] = \
                    map(dt_procedures.from_strdt_to_dt,
                        ast.literal_eval(row["cp_dts"]))

    # avoid reploting
    client_plotPath = {}

    for traceroute_type in unsupervised_utils.iter_traceroute_types():
        traceroute_field = "{}_filter".format(traceroute_type)
        valid_traceroute_field = "valid_{}".format(traceroute_type)

        utils.create_dirs(["{}/plots/paths/{}/{}/{}".format(script_dir, str_dt,
                                                            metric,
                                                            traceroute_type)])

        df = pd.read_csv("{}/prints/{}/filtered/traceroute_per_mac.csv".
                         format(script_dir, str_dt))
        cnt = 0
        for idx, row in df.iterrows():
            if row["valid_cnt_samples"] and row[valid_traceroute_field]:
                print ("cnt={}, traceroute_type={}, str_dt={}".
                       format(cnt, traceroute_type, str_dt))
                cnt += 1

                utils.create_dirs(["{}/plots/paths/{}/{}/{}/{}".
                                   format(script_dir, str_dt, metric,
                                          traceroute_type, row["server"])])

                traceroute = ast.literal_eval(row[traceroute_field])

                in_path = utils.get_in_path(row["server"], row["mac"],
                                            dt_start, dt_end)
                out_file_name = utils.get_out_file_name(row["server"],
                                                        row["mac"],
                                                        dt_start, dt_end)

                ts = TimeSeries(in_path, metric, dt_start, dt_end)
                ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
                ts_filter.percentile_filter(win_len=13, p=0.5)

                dir_path = "{}/plots/paths/{}/{}/{}/{}".format(script_dir,
                                                               str_dt,
                                                               metric,
                                                               traceroute_type,
                                                               row["server"])

                client = (row["server"], row["mac"])
                cp_dts = client_cps[client]

                for name in reversed(traceroute):
                    dir_path = "{}/{}".format(dir_path, name)
                    utils.create_dirs([dir_path])

                    out_path = "{}/{}.png".format(dir_path, out_file_name)

                    # avoid reploting
                    if client in client_plotPath:
                        shutil.copyfile(client_plotPath[client], out_path)
                    else:
                        client_plotPath[client] = out_path

                        plot_procedures.plot_ts_share_x(ts, ts_filter,
                                                        out_path,
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
    metric = "throughput_up"
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {"metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
