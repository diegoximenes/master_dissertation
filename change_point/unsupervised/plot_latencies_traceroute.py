import os
import sys
import datetime
import functools
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
import change_point.unsupervised.traceroute_exploratory_prints as \
    traceroute_exploratory_prints
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries


def get_name(name, ip_name, traceroute_type):
    name = traceroute_exploratory_prints.get_name(name, ip_name)
    if ("compress_embratel" in traceroute_type) and ("embratel" in name):
        return "embratel"
    return name


def get_ts_per_name(traceroute_type, ts_traceroute, dt_start, dt_end):
    update_ip_name = False
    ip_name = traceroute_exploratory_prints.get_ip_name(ts_traceroute.y)
    if not ip_name:
        update_ip_name = True

    name_ts = {}
    for i in xrange(len(ts_traceroute.y)):
        traceroute = ts_traceroute.y[i]

        if update_ip_name:
            ip_name = traceroute_exploratory_prints.get_ip_name([traceroute])

        ignore_traceroute = False
        for hop in traceroute:
            curr_name = None
            for name in hop["names"]:
                if name != u"##":
                    curr_name = name
            if curr_name:
                for name in hop["names"]:
                    if name == u"##":
                        ignore_traceroute = True
                if not ignore_traceroute:
                    name = get_name(hop["names"][0], ip_name, traceroute_type)
                    for j in xrange(1, len(hop["names"])):
                        curr_name = get_name(hop["names"][j], ip_name,
                                             traceroute_type)
                        if name != curr_name:
                            ignore_traceroute = True
        if ignore_traceroute:
            continue

        for hop in traceroute:
            name = hop["names"][0]
            if name != "##":
                name = get_name(name, ip_name, traceroute_type)

                if name not in name_ts:
                    name_ts[name] = TimeSeries(dt_start=dt_start,
                                               dt_end=dt_end)
                sum_latency = 0
                cnt_latency = 0
                for latency in hop["times"]:
                    if type(latency) == int:
                        sum_latency += latency / 1000.0
                        cnt_latency += 1
                if cnt_latency > 0:
                    mean_latency = sum_latency / cnt_latency
                else:
                    continue
                name_ts[name].x.append(ts_traceroute.x[i])
                name_ts[name].y.append(mean_latency)
    return name_ts


def plot_latencies_traceroute(dt_start, dt_end, preprocess_args):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/filtered/traceroute_per_mac.csv".format(script_dir,
                                                                    str_dt)
    df = pd.read_csv(in_path)
    for _, row, in df.iterrows():
        if row["valid_cnt_samples"]:
            in_path = utils.get_in_path(row["server"], row["mac"], dt_start,
                                        dt_end)
            ts_traceroute = TimeSeries(in_path=in_path, metric="traceroute",
                                       dt_start=dt_start, dt_end=dt_end)

            for traceroute_type in unsupervised_utils.iter_traceroute_types():
                valid_traceroute_field, traceroute_field = \
                    cp_utils.get_traceroute_fields(traceroute_type)
                if row[valid_traceroute_field]:
                    traceroute = ast.literal_eval(row[traceroute_field])
                    name_ts = get_ts_per_name(traceroute_type, ts_traceroute,
                                              dt_start, dt_end)

                    dir_path = ("{}/plots/paths/{}/{}/{}/{}".
                                format(script_dir, str_dt, "latency",
                                       traceroute_type, row["server"]))
                    traceroute_path = "/".join(map(str,
                                                   list(reversed(traceroute))))
                    dir_path = "{}/{}".format(dir_path, traceroute_path)

                    utils.create_dirs(["{}/traceroute_latencies/".
                                       format(dir_path),
                                       "{}/traceroute_latencies/{}".
                                       format(dir_path, row["mac"])])

                    for i in range(len(traceroute) - 1):
                        name = traceroute[i][0][0]
                        traceroute_path = "hop{}_{}".format(str(i).zfill(2),
                                                            name)
                        out_path = ("{}/traceroute_latencies/{}/{}.png".
                                    format(dir_path, row["mac"],
                                           traceroute_path))

                        ts_preprocessed = name_ts[name].copy()
                        cp_utils.preprocess(ts_preprocessed, preprocess_args)

                        plot_procedures.plot_ts_share_x(
                            name_ts[name],
                            ts_preprocessed,
                            out_path,
                            plot_type2="scatter",
                            title1="raw",
                            title2="median filtered",
                            default_ylabel=True)


def run_sequential(preprocess_args):
    for dt_start, dt_end in utils.iter_dt_range():
        plot_latencies_traceroute(dt_start, dt_end, preprocess_args)


def run_parallel(preprocess_args):
    dt_ranges = list(utils.iter_dt_range())
    fp = functools.partial(plot_latencies_traceroute,
                           preprocess_args=preprocess_args)
    utils.parallel_exec(fp, dt_ranges)


def run_single(dt_start, dt_end, preprocess_args):
    plot_latencies_traceroute(dt_start, dt_end, preprocess_args)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}

    parallel_args = {"preprocess_args": preprocess_args}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start,
                   "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
