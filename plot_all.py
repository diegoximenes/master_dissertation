import os
import sys
import datetime

sys.path.append("./import_scripts/")
import plot_procedures
from time_series import TimeSeries

# PARAMETERS
dt_start = datetime.datetime(2016, 5, 11)
num_days = 10
metric = "loss"

dt_end = dt_start + datetime.timedelta(days=num_days - 1)
date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
in_dir = "./change_point_detection/input/{}".format(date_dir)


def create_dirs():
    for dir in ["./plots/",
                "./plots/dtstart{}_dtend{}".format(dt_start, dt_end),
                "./plots/dtstart{}_dtend{}/filtered".format(dt_start, dt_end),
                "./plots/dtstart{}_dtend{}/not_filtered".format(dt_start,
                                                                dt_end)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def filter_ts(ts):
    min_fraction_of_measures = 0.85
    window_len = 48
    threshold = 0.01
    min_num_of_measures_greater_than_threshold_in_window = 6

    fraction_of_measures = float(len(ts.raw_x)) / (24 * 2 * num_days)
    if fraction_of_measures < min_fraction_of_measures:
        return False

    for i in range(window_len - 1, len(ts.raw_y)):
        cnt_greater_than_threshold = 0
        for j in range(i - window_len + 1, i):
            if ts.raw_y[j] > threshold:
                cnt_greater_than_threshold += 1
        if cnt_greater_than_threshold >= \
                min_num_of_measures_greater_than_threshold_in_window:
            return True

    return False


def process():
    create_dirs()
    for server in os.listdir(in_dir):
        print server
        for file_name in os.listdir("{}/{}".format(in_dir, server)):
            mac = file_name.split(".")[0]
            in_path = "{}/{}/{}".format(in_dir, server, file_name)
            out_path_filtered = ("./plots/dtstart{}_dtend{}/filtered/{}_{}"
                                 ".png").format(dt_start, dt_end, server, mac)
            out_path_not_filtered = ("./plots/dtstart{}_dtend{}/not_filtered/"
                                     "{}_{}.png").format(dt_start, dt_end,
                                                         server, mac)

            ts = TimeSeries(in_path, metric, dt_start, dt_end)

            if filter_ts(ts):
                out_path = out_path_filtered
            else:
                out_path = out_path_not_filtered
            plot_procedures.plot_ts(ts, out_path, ylim=[-0.02, 1.02],
                                    compress=False)

process()
