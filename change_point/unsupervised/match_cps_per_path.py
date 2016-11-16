import os
import sys
import ast
import datetime
import pandas as pd
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def match_cps_per_path(dt_start, dt_end, metric):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = ("{}/prints/{}/filtered/traceroute_per_mac.csv".
               format(script_dir, str_dt))
    df = pd.read_csv(in_path)
    mac_traceroute = {}
    for idx, row in df.iterrows():
        if row["is_unique_traceroute"]:
            mac_traceroute[row["mac"]] = \
                ast.literal_eval(row["traceroute_filtered"])

    write_dir = set()

    in_path = "{}/prints/{}/filtered/{}/match_cps.csv".format(script_dir,
                                                              str_dt, metric)
    df = pd.read_csv(in_path)
    for cnt, (idx, row) in enumerate(df.iterrows()):
        print "cnt={}/{}".format(cnt, df.shape[0])

        if row["server1"] != row["server2"]:
            continue

        server = row["server1"]
        mac1 = row["mac1"]
        mac2 = row["mac2"]

        if (mac1 not in mac_traceroute) or (mac2 not in mac_traceroute):
            continue

        dir_path = "{}/plots/paths/{}/{}/{}/".format(script_dir, str_dt,
                                                     metric, server)
        first_hop = True
        for name1, name2 in izip(mac_traceroute[mac1], mac_traceroute[mac2]):
            if (name1[0][0] is None) and (name2[0][0] is None) and first_hop:
                continue
            if (name1[0][0] is not None) and (name2[0][0] is not None):
                splitted1 = name1[0][0].split(".")
                splitted2 = name2[0][0].split(".")
                if (splitted1[0] == "192") and (splitted2[0] == "192"):
                    continue

            if name1 != name2:
                break

            first_hop = False
            dir_path = "{}/{}".format(dir_path, name1)
            utils.create_dirs([dir_path])
            out_path = "{}/matches_cps.csv".format(dir_path)

            if dir_path not in write_dir:
                with open(out_path, "w") as f:
                    l_period = ",{}" * (len(df.columns.values) - 1)
                    l_formatter = "{}" + l_period + "\n"
                    f.write(l_formatter.format(*df.columns.values))

            pd.DataFrame(row).T.to_csv(out_path, mode="a", header=False,
                                       index=False)

            write_dir.add(dir_path)


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)
    match_cps_per_path(dt_start, dt_end, metric)
