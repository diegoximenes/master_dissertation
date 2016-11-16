import sys
import os
import datetime
import ast
import functools
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def get_dts_empty_segs(str_empty_segs):
    empty_segs = ast.literal_eval(str_empty_segs)
    dts = [dt for seg in empty_segs for dt in seg]
    dts = map(dt_procedures.from_strdt_to_dt, dts)
    return dts


def match(match_type, row):
    if (row["tp"] == 0) or (row["fp"] > 0) or (row["fn"] > 0):
        return False
    if match_type == "cps":
        return row["type_cps1"] == row["type_cps2"]
    return True


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
    mac1_mac2 = set()
    for idx, row in df.iterrows():
        print "cnt={}".format(idx)

        mac_tp = (min(row["mac1"], row["mac2"]), max(row["mac1"], row["mac2"]))
        if (mac_tp not in mac1_mac2) and match(match_type, row):

            mac1_mac2.add(mac_tp)

            in_path1 = utils.get_in_path(row["server1"], row["mac1"], dt_start,
                                         dt_end)
            ts1 = TimeSeries(in_path1, metric, dt_start, dt_end)
            ts1.percentile_filter(win_len=13, p=0.5)

            in_path2 = utils.get_in_path(row["server2"], row["mac2"], dt_start,
                                         dt_end)
            ts2 = TimeSeries(in_path2, metric, dt_start, dt_end)
            ts2.percentile_filter(win_len=13, p=0.5)

            if match_type == "cps":
                cp_dts1 = ast.literal_eval(row["cp_dt1"])
                cp_dts2 = ast.literal_eval(row["cp_dt2"])
                cp_dts1 = map(dt_procedures.from_strdt_to_dt, cp_dts1)
                cp_dts2 = map(dt_procedures.from_strdt_to_dt, cp_dts2)
            else:
                cp_dts1 = get_dts_empty_segs(row["empty_segs1"])
                cp_dts2 = get_dts_empty_segs(row["empty_segs2"])

            out_file_name = ("server1{}_mac1{}_server2{}_mac2{}".
                             format(row["server1"], row["mac1"],
                                    row["server2"], row["mac2"]))
            out_path = "{}/plots/matches/{}/{}/{}/{}.png".format(script_dir,
                                                                 match_type,
                                                                 str_dt,
                                                                 metric,
                                                                 out_file_name)
            plot_procedures.plot_ts_share_x(ts1, ts2, out_path,
                                            dt_axvline1=cp_dts1,
                                            dt_axvline2=cp_dts2,
                                            plot_type2="scatter")


def run_parallel():
    dt_ranges = list(utils.iter_dt_range())
    fp_plot_matches = functools.partial(plot_matches, match_type="empty_segs")
    utils.parallel_exec(fp_plot_matches, dt_ranges)
    fp_plot_matches = functools.partial(plot_matches, match_type="cps")
    utils.parallel_exec(fp_plot_matches, dt_ranges)


def run_sequential():
    for dt_start, dt_end in utils.iter_dt_range():
        plot_matches(dt_start, dt_end, metric, "empty_segs")
        plot_matches(dt_start, dt_end, metric, "cps")


def run_single(metric, dt_start, dt_end):
    # plot_matches(dt_start, dt_end, metric, "empty_segs")
    plot_matches(dt_start, dt_end, metric, "cps")

if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(metric, dt_start, dt_end)
    # run_parallel(metric)
    # run_sequential(metric)
