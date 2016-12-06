import os
import sys
import datetime
import ast
import functools
import pandas as pd
from operator import itemgetter
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.dt_procedures as dt_procedures
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
import change_point.cp_utils.cp_utils as cp_utils


def voting(dt_start, dt_end, metric, in_dir, eps_hours):
    """
    By now I assume that the cps from a single time series are more than
    eps_hours apart
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_dir = "{}/plots/{}/{}/{}".format(script_dir, in_dir, str_dt, metric)
    for dir_path, _, file_names in os.walk(in_dir):
        if "cps_per_mac.csv" in file_names:
            with open("{}/match_cps.csv".format(dir_path), "w") as f:
                f.write("cp_dt_start,cp_dt_end,cp_type,fraction_of_clients,"
                        "cnt_clients,clients\n")

                df = pd.read_csv("{}/cps_per_mac.csv".format(dir_path))
                cnt_clients = df.shape[0]

                for cp_type in cp_utils.iter_cp_types():
                    l = []
                    for idx, row in df.iterrows():
                        cp_dts = []
                        cp_dts_aux = map(dt_procedures.from_strdt_to_dt,
                                         ast.literal_eval(row["cp_dt"]))
                        cp_types_aux = ast.literal_eval(row["type_cps"])
                        for i_cp_dt, i_cp_type in izip(cp_dts_aux,
                                                       cp_types_aux):
                            if i_cp_type == cp_type:
                                cp_dts.append(i_cp_dt)

                        l = l + map(lambda dt: {"dt": dt, "mac": row["mac"],
                                                "server": row["server"]},
                                    cp_dts)
                    l.sort(key=itemgetter("dt"))

                    votes = \
                        unsupervised_utils.multiple_inexact_voting(
                            l, eps_hours)
                    for vote in votes:
                        clients = map(lambda dic: {"mac": dic["mac"],
                                                   "server":
                                                   dic["server"]},
                                      vote["interval"])
                        l_dt = vote["l_dt"]
                        r_dt = vote["r_dt"]

                        fraction_of_clients = \
                            float(len(clients)) / cnt_clients

                        f.write("{},{},{},{},{},\"{}\"\n".
                                format(l_dt, r_dt, cp_type,
                                       fraction_of_clients,
                                       len(clients), clients))


def run_parallel(metric, eps_hours):
    dt_ranges = list(utils.iter_dt_range())

    fp_voting = functools.partial(voting, metric=metric, in_dir="paths",
                                  eps_hours=eps_hours)
    utils.parallel_exec(fp_voting, dt_ranges)

    fp_voting = functools.partial(voting, metric=metric, in_dir="names",
                                  eps_hours=eps_hours)
    utils.parallel_exec(fp_voting, dt_ranges)


def run_sequential(metric, eps_hours):
    for dt_start, dt_end in utils.iter_dt_range():
        voting(dt_start, dt_end, metric, "paths", eps_hours)
        voting(dt_start, dt_end, metric, "names", eps_hours)


def run_single(dt_start, dt_end, metric, eps_hours):
    voting(dt_start, dt_end, metric, "paths", eps_hours)
    voting(dt_start, dt_end, metric, "names", eps_hours)


if __name__ == "__main__":
    eps_hours = 4
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    parallel_args = {"metric": metric, "eps_hours": eps_hours}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args)
