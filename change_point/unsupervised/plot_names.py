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


def plot_per_name(dt_start, dt_end, metric):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/names".format(script_dir),
                       "{}/plots/names/{}".format(script_dir, dt_dir)])

    df = pd.read_csv("{}/prints/{}/traceroute_per_mac_filtered.csv".
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

            utils.create_dirs(["{}/plots/names/{}/{}".format(script_dir,
                                                             dt_dir, name)])

            in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir,
                                                     row["server"], row["mac"])
            out_file_name = utils.get_out_file_name(row["server"], row["mac"],
                                                    dt_start, dt_end)
            out_path = "{}/plots/names/{}/{}/{}.png".format(script_dir,
                                                            dt_dir,
                                                            name,
                                                            out_file_name)
            ts = TimeSeries(in_path, metric, dt_start, dt_end)
            plot_procedures.plot_ts(ts, out_path)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)
    plot_per_name(dt_start, dt_end, "loss")
