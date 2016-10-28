import sys
import os
import datetime
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def plot_matches(dt_start, dt_end, metric, match_type):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/matches".format(script_dir),
                       "{}/plots/matches/{}".format(script_dir, match_type),
                       "{}/plots/matches/{}/{}".format(script_dir, match_type,
                                                       str_dt),
                       "{}/plots/matches/{}/{}/{}".format(script_dir,
                                                          match_type,
                                                          str_dt, metric)])

    in_path = "{}/prints/{}/filtered/{}/match_{}.csv".format(script_dir,
                                                             str_dt, metric,
                                                             match_type)
    df = pd.read_csv(in_path)
    macServer1_macServer2 = set()
    for idx, row in df.iterrows():
        print "cnt={}".format(idx)

        if (row["tp"] > 0) and (row["fp"] == 0) and (row["fn"] == 0):
            tp1 = (row["mac1"], row["server1"])
            tp2 = (row["mac2"], row["server2"])
            macServer1_macServer2.add((min(tp1, tp2), max(tp1, tp2)))

    for cnt, (tp1, tp2) in enumerate(macServer1_macServer2):
        print "cnt={}/{}".format(cnt, len(macServer1_macServer2))

        mac1, server1 = tp1
        mac2, server2 = tp2

        in_path1 = utils.get_in_path(server1, mac1, dt_start, dt_end)
        ts1 = TimeSeries(in_path1, metric, dt_start, dt_end)
        ts1.percentile_filter(win_len=13, p=0.5)

        in_path2 = utils.get_in_path(server2, mac2, dt_start, dt_end)
        ts2 = TimeSeries(in_path2, metric, dt_start, dt_end)
        ts2.percentile_filter(win_len=13, p=0.5)

        if match_type == "cps":
            cp_dts1 = ast.literal_eval(row["cp_dt1"])
            cp_dts2 = ast.literal_eval(row["cp_dt2"])
        else:
            cp_dts1 = ast.literal_eval(row["empty_segs1"])
            cp_dts2 = ast.literal_eval(row["empty_segs2"])
        # cp_dts1 = map(dt_procedures.from_strdt_to_dt, cp_dts1)
        # cp_dts2 = map(dt_procedures.from_strdt_to_dt, cp_dts2)

        print "server1={}, mac1={}, cp_dts1={}".format(server1, mac1, cp_dts1)
        print "server2={}, mac2={}, cp_dts2={}".format(server2, mac2, cp_dts2)
        print "###########"

        out_file_name = "server1{}_mac1{}_server2{}_mac2{}".format(server1,
                                                                   mac1,
                                                                   server2,
                                                                   mac2)
        out_path = "{}/plots/matches/{}/{}/{}/{}.png".format(script_dir,
                                                             match_type,
                                                             str_dt,
                                                             metric,
                                                             out_file_name)
        plot_procedures.plot_ts_share_x(ts1, ts2, out_path,
                                        dt_axvline1=cp_dts1,
                                        dt_axvline2=cp_dts2, compress=False,
                                        plot_type2="scatter")


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)

    # plot_matches(dt_start, dt_end, metric, "empty_segs")
    plot_matches(dt_start, dt_end, metric, "cps")
