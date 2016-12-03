import os
import sys
import datetime
import ast
import copy
import functools
import pandas as pd
from operator import itemgetter

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.dt_procedures as dt_procedures


def multiple_inexact_voting_totally_ordered(dt_start, dt_end, metric,
                                            in_dir, eps_hours):
    """
    By now I assume that the cps from a single time series are more than
    eps_hours apart
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_dir = "{}/plots/{}/{}/{}".format(script_dir, in_dir, str_dt, metric)
    for dir_path, _, file_names in os.walk(in_dir):
        if "cps_per_mac.csv" in file_names:
            l = []
            df = pd.read_csv("{}/cps_per_mac.csv".format(dir_path))
            cnt_clients = df.shape[0]
            for idx, row in df.iterrows():
                cp_dts = map(dt_procedures.from_strdt_to_dt,
                             ast.literal_eval(row["cp_dt"]))
                l = l + map(lambda dt: {"dt": dt, "mac": row["mac"],
                                        "server": row["server"]}, cp_dts)
            l.sort(key=itemgetter("dt"))

            with open("{}/match_cps.csv".format(dir_path), "w") as f:
                f.write("cp_dt_start,cp_dt_end,fraction_of_clients,clients\n")
                while l:
                    i = j = len_max_maximal_interval = 0
                    max_maximal_interval = []
                    while j < len(l):
                        while ((j < len(l)) and
                               dt_procedures.dt_is_close(l[i]["dt"],
                                                         l[j]["dt"],
                                                         eps_hours)):
                            j += 1
                        if j - i > len_max_maximal_interval:
                            len_max_maximal_interval = j - i
                            max_maximal_interval = [i, j - 1]
                        i += 1

                    clients = map(lambda dic: {"mac": dic["mac"],
                                               "server": dic["server"]},
                                  l[max_maximal_interval[0]:
                                    max_maximal_interval[1] + 1])

                    l_dt = l[max_maximal_interval[0]]["dt"]
                    r_dt = l[max_maximal_interval[1]]["dt"]

                    fraction_of_clients = float(len(clients)) / cnt_clients

                    f.write("{},{},{},\"{}\"\n".format(l_dt, r_dt,
                                                       fraction_of_clients,
                                                       clients))

                    l_aux = copy.deepcopy(l)
                    l = []
                    for dic in l_aux:
                        if (dic["dt"] < l_dt) or (dic["dt"] > r_dt):
                            l.append(dic)


def run_parallel(metric, eps_hours):
    dt_ranges = list(utils.iter_dt_range())

    fp_multiple_inexact_voting_totally_ordered = \
        functools.partial(multiple_inexact_voting_totally_ordered,
                          metric=metric, in_dir="paths", eps_hours=eps_hours)
    utils.parallel_exec(fp_multiple_inexact_voting_totally_ordered, dt_ranges)

    fp_multiple_inexact_voting_totally_ordered = \
        functools.partial(multiple_inexact_voting_totally_ordered,
                          metric=metric, in_dir="names", eps_hours=eps_hours)
    utils.parallel_exec(fp_multiple_inexact_voting_totally_ordered, dt_ranges)


def run_sequential(metric, eps_hours):
    for dt_start, dt_end in utils.iter_dt_range():
        multiple_inexact_voting_totally_ordered(dt_start, dt_end, metric,
                                                "paths", eps_hours)
        multiple_inexact_voting_totally_ordered(dt_start, dt_end, metric,
                                                "names", eps_hours)


def run_single(dt_start, dt_end, metric, eps_hours):
    multiple_inexact_voting_totally_ordered(dt_start, dt_end, metric,
                                            "paths", eps_hours)
    multiple_inexact_voting_totally_ordered(dt_start, dt_end, metric,
                                            "names", eps_hours)


if __name__ == "__main__":
    eps_hours = 4
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(dt_start, dt_end, metric, eps_hours)
    # run_parallel(metric, eps_hours)
    # run_sequential(metric, eps_hours)
