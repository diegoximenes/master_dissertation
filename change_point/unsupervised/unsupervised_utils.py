import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.utils.cp_utils as cp_utils


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

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)

    path_dirs = set()

    in_path = "{}/prints/{}/filtered/{}/{}".format(script_dir, str_dt, metric,
                                                   file_name)
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac = row["mac"]
        server = row["server"]
        traceroute = mac_traceroute[mac]

        dir_path = "{}/plots/paths/{}/{}/{}/".format(out_dir, str_dt,
                                                     metric, server)
        utils.create_dirs([dir_path])

        first_hop = True
        for name in reversed(traceroute):
            if (name[0][0] is None) and first_hop:
                continue
            splitted = name[0][0].split(".")
            if splitted[0] == "192":
                continue
            first_hop = False

            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/{}".format(dir_path, file_name)
            if dir_path not in path_dirs:
                create_csv_with_same_header(out_path, df)
            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)
            path_dirs.add(dir_path)


def print_per_name(dt_start, dt_end, metric, file_name):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_dir = "{}/change_point/unsupervised/".format(base_dir)
    utils.create_dirs(["{}/plots".format(out_dir),
                       "{}/plots/names/".format(out_dir),
                       "{}/plots/names/{}".format(out_dir, str_dt),
                       "{}/plots/names/{}/{}".format(out_dir, str_dt,
                                                     metric)])

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)

    name_dirs = set()

    in_path = "{}/prints/{}/filtered/{}/{}".format(script_dir, str_dt, metric,
                                                   file_name)
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac = row["mac"]
        server = row["server"]
        traceroute = mac_traceroute[mac]

        dir_path = "{}/plots/names/{}/{}/{}/".format(out_dir, str_dt,
                                                     metric, server)
        utils.create_dirs([dir_path])

        for name in cp_utils.iter_names_traceroute_filtered(traceroute):
            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/{}".format(dir_path, file_name)
            if dir_path not in name_dirs:
                create_csv_with_same_header(out_path, df)
            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)
            name_dirs.add(dir_path)
