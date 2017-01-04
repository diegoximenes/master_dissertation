import os
import sys
import copy
import ast
import pandas as pd
from collections import defaultdict

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.dt_procedures as dt_procedures
import change_point.cp_utils.cp_utils as cp_utils


def get_client_cps(plot_cps, str_dt, metric):
    # get client->cps mapping
    client_cps = defaultdict(list)
    if plot_cps:
        in_path = "{}/prints/{}/filtered/{}/cps_per_mac.csv".format(script_dir,
                                                                    str_dt,
                                                                    metric)
        if os.path.isfile(in_path):
            df = pd.read_csv(in_path)
            for idx, row in df.iterrows():
                client = utils.get_client(row["server"], row["mac"])
                client_cps[client] = map(dt_procedures.from_strdt_to_dt,
                                         ast.literal_eval(row["cp_dts"]))
    return client_cps


def iter_traceroute_types():
    # this order must be preserved
    traceroute_types = \
        ["traceroute_compress_embratel",
         "traceroute_compress_embratel_without_last_hop_embratel",
         "traceroute_without_embratel"]
    for traceroute in traceroute_types:
        yield traceroute


def multiple_inexact_voting(l, eps_hours):
    """
    multiple inexact voting totally ordered
    """

    ret = []
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

        l_dt = l[max_maximal_interval[0]]["dt"]
        r_dt = l[max_maximal_interval[1]]["dt"]

        elem = {}
        elem["interval"] = copy.deepcopy(
            l[max_maximal_interval[0]:max_maximal_interval[1] + 1])
        elem["l_dt"] = l_dt
        elem["r_dt"] = r_dt
        ret.append(elem)

        l_aux = copy.deepcopy(l)
        l = []
        for dic in l_aux:
            if (dic["dt"] < l_dt) or (dic["dt"] > r_dt):
                l.append(dic)
    return ret


def create_csv_with_same_header(out_path, df):
    with open(out_path, "w") as f:
        l_period = ",{}" * (len(df.columns.values) - 1)
        l_formatter = "{}" + l_period + "\n"
        f.write(l_formatter.format(*df.columns.values))


def print_per_path(dt_start, dt_end, metric, file_name):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_dir = "{}/change_point/unsupervised/".format(base_dir)
    utils.create_dirs(["{}/plots".format(out_dir),
                       "{}/plots/paths".format(out_dir),
                       "{}/plots/paths/{}".format(out_dir, str_dt),
                       "{}/plots/paths/{}/{}".format(out_dir, str_dt,
                                                     metric)])

    in_path = "{}/prints/{}/filtered/{}/{}".format(script_dir, str_dt, metric,
                                                   file_name)

    for traceroute_type in iter_traceroute_types():
        valid_traceroute_field, traceroute_field = \
            cp_utils.get_traceroute_fields(traceroute_type)

        client_traceroute = cp_utils.get_client_traceroute(dt_start, dt_end,
                                                           traceroute_type)

        path_dirs = set()

        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            client = utils.get_client(row["server"], row["mac"])
            if client in client_traceroute:
                traceroute = client_traceroute[client]

                dir_path = "{}/plots/paths/{}/{}/{}/{}".format(out_dir, str_dt,
                                                               metric,
                                                               traceroute_type,
                                                               row["server"])
                utils.create_dirs([dir_path])

                for name in reversed(traceroute):
                    if name[0][0].split(".")[0] == "192":
                        continue

                    dir_path = "{}/{}".format(dir_path, name)
                    utils.create_dirs([dir_path])

                    out_path = "{}/{}".format(dir_path, file_name)
                    if dir_path not in path_dirs:
                        create_csv_with_same_header(out_path, df)
                    pd.DataFrame(row).T.to_csv(out_path, mode="a",
                                               header=False, index=False)
                    path_dirs.add(dir_path)


def print_per_name(dt_start, dt_end, metric, file_name):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_dir = "{}/change_point/unsupervised/".format(base_dir)
    utils.create_dirs(["{}/plots".format(out_dir),
                       "{}/plots/names/".format(out_dir),
                       "{}/plots/names/{}".format(out_dir, str_dt),
                       "{}/plots/names/{}/{}".format(out_dir, str_dt,
                                                     metric)])

    in_path = "{}/prints/{}/filtered/{}/{}".format(script_dir, str_dt, metric,
                                                   file_name)

    for traceroute_type in iter_traceroute_types():
        valid_traceroute_field, traceroute_field = \
            cp_utils.get_traceroute_fields(traceroute_type)

        client_traceroute = cp_utils.get_client_traceroute(dt_start, dt_end,
                                                           traceroute_type)

        name_dirs = set()

        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            client = utils.get_client(row["server"], row["mac"])
            if client in client_traceroute:
                traceroute = client_traceroute[client]

                dir_path = "{}/plots/names/{}/{}/{}/{}".format(out_dir, str_dt,
                                                               metric,
                                                               traceroute_type,
                                                               row["server"])
                utils.create_dirs([dir_path])

                for name in cp_utils.iter_names_traceroute_filtered(
                        traceroute):
                    name_path = "{}/{}".format(dir_path, name)
                    utils.create_dirs([name_path])

                    out_path = "{}/{}".format(name_path, file_name)
                    if name_path not in name_dirs:
                        create_csv_with_same_header(out_path, df)
                    pd.DataFrame(row).T.to_csv(out_path, mode="a",
                                               header=False, index=False)
                    name_dirs.add(name_path)
