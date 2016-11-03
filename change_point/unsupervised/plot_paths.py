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
from utils.time_series import TimeSeries


def plot_per_path(dt_start, dt_end, metric):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/paths".format(script_dir),
                       "{}/plots/paths/{}".format(script_dir, str_dt),
                       "{}/plots/paths/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    df = pd.read_csv("{}/prints/{}/filtered/traceroute_per_mac.csv".
                     format(script_dir, str_dt))
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        traceroute = ast.literal_eval(row["traceroute_filtered"])

        in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir,
                                                 row["server"], row["mac"])
        out_file_name = utils.get_out_file_name(row["server"], row["mac"],
                                                dt_start, dt_end)

        ts = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter.percentile_filter(win_len=13, p=0.5)

        dir_path = "{}/plots/paths/{}/{}".format(script_dir, str_dt, metric)
        for name in reversed(traceroute):
            dir_path = "{}/{}".format(dir_path, name)
            utils.create_dirs([dir_path])

            out_path = "{}/{}.png".format(dir_path, out_file_name)

            plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
                                            compress=False,
                                            plot_type2="scatter")


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    plot_per_path(dt_start, dt_end, metric)

    # for metric in ["loss", "latency", "throughput_down", "throughput_up"]:
    #     for dt_start, dt_end in utils.iter_dt_range():
    #         plot_per_path(dt_start, dt_end, metric)
