import sys
import os
import datetime
import ast
import functools
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.cp_utils.cp_utils as cp_utils
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
from utils.time_series import TimeSeries


def plot_per_name(dt_start, dt_end, metric, only_cmts, plot_cps):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/names".format(script_dir),
                       "{}/plots/names/{}".format(script_dir, str_dt),
                       "{}/plots/names/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    client_cps = unsupervised_utils.get_client_cps(plot_cps, str_dt, metric)

    for traceroute_type in unsupervised_utils.iter_traceroute_types():
        valid_traceroute_field, traceroute_field = \
            cp_utils.get_traceroute_fields(traceroute_type)

        utils.create_dirs(["{}/plots/names/{}/{}/{}".format(script_dir, str_dt,
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

                for name in cp_utils.iter_names_traceroute_filtered(
                        ast.literal_eval(row[traceroute_field])):

                    cp_dts = {}
                    if plot_cps:
                        client = utils.get_client(row["server"], row["mac"])
                        cp_dts = client_cps[client]

                    utils.create_dirs(["{}/plots/names/{}/{}/{}/{}".
                                       format(script_dir, str_dt, metric,
                                              traceroute_type, row["server"]),
                                       "{}/plots/names/{}/{}/{}/{}/{}".
                                       format(script_dir, str_dt, metric,
                                              traceroute_type, row["server"],
                                              name)])

                    in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir,
                                                             row["server"],
                                                             row["mac"])
                    out_file_name = utils.get_out_file_name(row["server"],
                                                            row["mac"],
                                                            dt_start, dt_end)
                    out_path = ("{}/plots/names/{}/{}/{}/{}/{}/{}.png".
                                format(script_dir, str_dt, metric,
                                       traceroute_type, row["server"], name,
                                       out_file_name))

                    ts = TimeSeries(in_path, metric, dt_start, dt_end)
                    ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
                    ts_filter.percentile_filter(win_len=13, p=0.5)
                    plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
                                                    compress=False,
                                                    plot_type2="scatter",
                                                    dt_axvline1=cp_dts,
                                                    dt_axvline2=cp_dts)


def run_parallel(metric):
    dt_ranges = list(utils.iter_dt_range())
    f_plot_per_name = functools.partial(plot_per_name, metric=metric,
                                        only_cmts=False, plot_cps=True)
    utils.parallel_exec(f_plot_per_name, dt_ranges)


def run_sequential(metric):
    for dt_start, dt_end in utils.iter_dt_range():
        plot_per_name(dt_start, dt_end, metric, False, True)


def run_single(metric, dt_start, dt_end):
    plot_per_name(dt_start, dt_end, metric, False, True)


if __name__ == "__main__":
    metric = "latency"
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
