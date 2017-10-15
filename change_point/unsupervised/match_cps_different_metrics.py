import os
import sys
import datetime
import functools
import ast
import pandas as pd
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
import change_point.cp_utils.cp_utils as cp_utils


def match_cps_different_metrics(dt_start, dt_end, eps_hours):
    """
    by now disconsider event type
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)

    client_metric_cps = {}
    in_dir = "{}/prints/{}/filtered".format(script_dir, str_dt)
    for metric in os.listdir(in_dir):
        in_path = "{}/prints/{}/filtered/{}".format(script_dir, str_dt, metric)
        df = pd.read_csv(in_path)
        for _, row in df.iterrows():
            client = utils.get_client(row["server"], row["mac"])
            if client not in client_metric_cps:
                client_metric_cps[client] = {}
            client_metric_cps[client][metric] = \
                {"cp_dts": ast.literal_eval(row["cp_dts"]),
                 "type_cps": ast.literal_eval(row["type_cps"])}

    for client in client_metric_cps:
        for metric in client_metric_cps[client]:
            l = []
            for cp_dt, cp_type in izip(client_metric_cps[client][metric]["cp_dts"], client_metric_cps[client][metric]["type_cps"):


def run_parallel(metric, eps_hours):
    dt_ranges = list(utils.iter_dt_range())

    fp = functools.partial(match_cps_different_metrics, eps_hours=eps_hours)
    utils.parallel_exec(fp, dt_ranges)


def run_sequential(metric, eps_hours):
    for dt_start, dt_end in utils.iter_dt_range():
        match_cps_different_metrics(dt_start, dt_end, eps_hours)


def run_single(dt_start, dt_end, metric, eps_hours):
    match_cps_different_metrics(dt_start, dt_end, eps_hours)


if __name__ == "__main__":
    eps_hours = 4
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {"eps_hours": eps_hours}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
