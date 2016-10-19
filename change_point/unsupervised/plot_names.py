import sys
import os
import datetime
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries


def create_dirs(date_dir, name):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/names".format(script_dir, date_dir),
                "{}/plots/names/{}".format(script_dir, date_dir),
                "{}/plots/names/{}/{}".format(script_dir, date_dir, name)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def plot(dt_start, dt_end):
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))

    df = pd.read_csv("{}/prints/{}/traceroute_per_mac_filtered.csv".
                     format(script_dir, date_dir))
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

            create_dirs(date_dir, name)

            in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir,
                                                     row["server"], row["mac"])
            out_path = "{}/plots/names/{}/{}/{}.png".format(script_dir,
                                                            date_dir,
                                                            name,
                                                            row["mac"])
            ts = TimeSeries(in_path, "loss", dt_start, dt_end)
            plot_procedures.plot_ts(ts, out_path, ylim=[-0.02, 1.02])

if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 8, 1)
    plot(dt_start, dt_end)
