import os
import sys

sys.path.append("../../import_scripts/")
import plot_procedures
import time_series
from time_series import TimeSeries

# PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
window_len = 10
metric_binRange = {}
metric_binRange["loss"] = [0.01, 0.05, 1.0]

date_dir = str(target_year) + "_" + str(target_month).zfill(2)


def create_dirs(server):
    if not os.path.exists("./plots/"):
        os.makedirs("./plots/")
    if not os.path.exists("./plots/sliding_window_single_window/"):
        os.makedirs("./plots/sliding_window_single_window/")
    if not os.path.exists("./plots/sliding_window_single_window/" + date_dir):
        os.makedirs("./plots/sliding_window_single_window/" + date_dir)
    if not os.path.exists("./plots/sliding_window_single_window/" + date_dir +
                          "/" + server):
        os.makedirs("./plots/sliding_window_single_window/" + date_dir + "/" +
                    server)


def get_bin(measure):
    for bin in range(len(metric_binRange[metric])):
        if measure <= metric_binRange[metric][bin]:
            return bin


def get_state(l):
    """
    work only for 3 states
    """

    bin_cnt = {}
    for bin in range(len(metric_binRange[metric])):
        bin_cnt[bin] = 0

    for i in l:
        bin_cnt[get_bin(i)] += 1
    for bin in bin_cnt:
        bin_cnt[bin] /= float(len(l))

    if bin_cnt[2] >= 0.35:
        return 2  # bad
    if bin_cnt[0] >= 0.80:
        return 0  # good
    return 1  # medium


def sliding_window(in_file_path, out_file_path):
    ts = TimeSeries(in_file_path, target_month, target_year, metric)
    ts_compressed = time_series.get_compressed(ts)

    ts_state = time_series.dist_ts(ts)
    for i in range(window_len - 1, len(ts_compressed.y)):
        dt = ts_compressed.x[i]
        state = get_state(ts_compressed.y[i - (window_len - 1):i])

        ts_state.dt_mean[dt] = state
        ts_state.x.append(dt)
        ts_state.y.append(state)
    plot_procedures.plot_ts_and_dist(ts, ts_state, out_file_path + ".png",
                                     ylabel=metric, dist_ylabel="states",
                                     dist_plot_type="scatter",
                                     dist_ylim=[0 - 0.5,
                                                len(metric_binRange[metric]) -
                                                1 + 0.5],
                                     dist_yticks=range(len(metric_binRange[
                                         metric])),
                                     dist_yticklabels=["good", "medium",
                                                       "bad"])


def get_change_points():
    cnt = 0

    mac = "64:66:B3:50:03:A2"
    server = "NHODTCSRV04"
    sliding_window("../input/" + date_dir + "/" + server + "/" + mac + ".csv",
                   "./test_single_window")
    return

    for server in os.listdir("../input/" + date_dir + "/"):
        print server
        create_dirs(server)
        for file_name in os.listdir("../input/%s/%s" % (date_dir, server)):
            mac = file_name.split(".")[0]
            cnt += 1
            print "cnt=" + str(cnt)

            in_file_path = "../input/%s/%s/%s.csv" % (date_dir, server, mac)
            out_file_path = ("./plots/sliding_window_single_window/%s/%s/%s" %
                             (date_dir, server, mac))

            sliding_window(in_file_path, out_file_path)

get_change_points()
