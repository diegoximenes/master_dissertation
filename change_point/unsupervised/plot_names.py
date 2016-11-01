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


def is_cmts(name):
    ip1 = name[0][1]
    ip2 = name[1][1]
    if utils.is_private_ip(ip1) and (not utils.is_private_ip(ip2)):
        return True
    return False


def plot_per_name(dt_start, dt_end, metric, only_cmts):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/names".format(script_dir),
                       "{}/plots/names/{}".format(script_dir, str_dt),
                       "{}/plots/names/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    df = pd.read_csv("{}/prints/{}/filtered/traceroute_per_mac.csv".
                     format(script_dir, str_dt))
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)
        traceroute = ast.literal_eval(row["traceroute_filtered"])
        for name in traceroute:
            if name[0][0] is None:
                continue
            splitted = name[0][0].split(".")
            if splitted[0] == "192" and splitted[1] == "168":
                continue

            if only_cmts and (not is_cmts(name)):
                continue

            utils.create_dirs(["{}/plots/names/{}/{}/{}".format(script_dir,
                                                                str_dt, metric,
                                                                name)])

            in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir,
                                                     row["server"], row["mac"])
            out_file_name = utils.get_out_file_name(row["server"], row["mac"],
                                                    dt_start, dt_end)
            out_path = "{}/plots/names/{}/{}/{}/{}.png".format(script_dir,
                                                               str_dt,
                                                               metric,
                                                               name,
                                                               out_file_name)

            ts = TimeSeries(in_path, metric, dt_start, dt_end)
            ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
            ts_filter.percentile_filter(win_len=13, p=0.5)
            plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
                                            compress=False,
                                            plot_type2="scatter")


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)
    plot_per_name(dt_start, dt_end, metric, True)
