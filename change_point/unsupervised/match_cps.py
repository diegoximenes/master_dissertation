import os
import sys
import ast
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.read_input as read_input
import change_point.utils.cmp_class as cmp_class
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def match_cps(dt_start, dt_end, metric, hours_tol, filtered):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/{}/{}/cps_per_mac.csv".format(script_dir, str_dt,
                                                          filtered, metric)

    mac_cps = {}
    mac_server = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        str_dts = ast.literal_eval(row["cp_dt"])
        dts = []
        for strdt in str_dts:
            dts.append(dt_procedures.from_strdt_to_dt(strdt))
        mac_cps[row["mac"]] = dts
        mac_server[row["mac"]] = row["server"]

    out_path = "{}/prints/{}/{}/{}/match_cps.csv".format(script_dir, str_dt,
                                                         filtered, metric)
    with open(out_path, "w") as f:
        f.write("server1,server2,mac1,mac2,tp,fp,fn,cp_dt1,cp_dt2\n")

        cnt = 0
        for mac1 in mac_cps:
            cnt += 1
            print "cnt={}".format(cnt)

            for mac2 in mac_cps:
                if mac1 != mac2:
                    str_cps1 = map(str, mac_cps[mac1])
                    str_cps2 = map(str, mac_cps[mac2])

                    # only tp, fp, fn are correct with this parameters
                    ts = TimeSeries()
                    conf = cmp_class.conf_mat(mac_cps[mac1], mac_cps[mac2], ts,
                                              dt_procedures.dt_is_close,
                                              hours_tol)
                    formatter = "{}" + ",{}" * 6 + ",\"{}\"" * 2 + "\n"
                    f.write(formatter.format(mac_server[mac1],
                                             mac_server[mac2],
                                             mac1,
                                             mac2,
                                             conf["tp"],
                                             conf["fp"],
                                             conf["fn"],
                                             str_cps1,
                                             str_cps2))

    utils.sort_csv_file(out_path, ["tp", "fp", "fn"],
                        ascending=[False, True, True])


def print_cps_per_mac(dt_start, dt_end, dir_model, metric, filtered):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/prints/".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt),
                       "{}/prints/{}/{}".format(script_dir, str_dt, filtered),
                       "{}/prints/{}/{}/{}".format(script_dir, str_dt,
                                                   filtered, metric)])

    out_path = "{}/prints/{}/{}/{}/cps_per_mac.csv".format(script_dir, str_dt,
                                                           filtered, metric)
    with open(out_path, "w") as f:
        f.write("server,mac,cp_dt\n")
        in_path_dir = ("{}/change_point/models/{}/plots/unsupervised/{}/{}".
                       format(base_dir, dir_model, str_dt, metric))

        target_macs = read_input.get_macs_traceroute_filter(dt_start, dt_end,
                                                            filtered)

        cnt = 0
        for file_name in os.listdir(in_path_dir):
            if ".csv" in file_name:
                cnt += 1
                print "cnt={}".format(cnt)

                server = file_name.split("server")[1].split("_")[0]
                mac = file_name.split("mac")[1].split("_")[0]

                if mac not in target_macs:
                    continue

                cps = []
                df = pd.read_csv("{}/{}".format(in_path_dir, file_name))
                for idx, row in df.iterrows():
                    cps.append(row["dt"])
                f.write("{},{},\"{}\"\n".format(server, mac, cps))


if __name__ == "__main__":
    metric = "latency"
    dir_model = "seg_neigh"
    hours_tol = 4
    filtered = "filtered"

    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)
    print_cps_per_mac(dt_start, dt_end, dir_model, metric, filtered)
    match_cps(dt_start, dt_end, metric, hours_tol, filtered)
