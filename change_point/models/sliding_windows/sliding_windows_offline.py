import os
import sys
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils
import change_point.utils.cmp_win as cmp_win
import change_point.models.change_point_alg as change_point_alg
from utils.time_series import TimeSeries

script_dir = os.path.join(os.path.dirname(__file__), ".")


class SlidingWindowsOffline(change_point_alg.ChangePointAlg):
    def __init__(self, preprocess_args, win_len, thresh, min_peak_dist, f_dist,
                 bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
        self.preprocess_args = preprocess_args
        self.win_len = win_len
        self.thresh = thresh
        self.min_peak_dist = min_peak_dist
        self.f_dist = cp_utils.get_f_dist(f_dist, bin_size_f_dist,
                                          min_bin_f_dist, max_bin_f_dist)

    def get_ts_dist(self, ts):
        ts_dist = time_series.dist_ts(ts)
        for i in xrange(self.win_len, len(ts.y) - self.win_len + 1):
            win1 = ts.y[i - self.win_len:i]
            win2 = ts.y[i:i + self.win_len]
            dist = self.f_dist(win1, win2)
            ts_dist.x.append(ts.x[i])
            ts_dist.y.append(dist)
        return ts_dist

    def fit(self, df):
        pass

    def predict(self, ts):
        ts_dist = self.get_ts_dist(ts)
        dist_peaks = cp_utils.detect_peaks(ts_dist.y, mph=self.thresh,
                                           mpd=self.min_peak_dist)
        # dist_peaks have the indexes of the peaks in the ts_dist, however the
        # change points are represented as the indexes of the ts
        cps = np.asarray(dist_peaks) + self.win_len
        return cps


def create_dirs():
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/offline/".format(script_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"win_len": 20,
             "thresh": 0.1,
             "min_peak_dist": 10,
             "f_dist": cmp_win.mean_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}

    sliding_windows = SlidingWindowsOffline(preprocess_args=preprocess_args,
                                            **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        ts = cp_utils.get_ts(row, preprocess_args)
        pred = sliding_windows.predict(ts)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        ts_dist = sliding_windows.get_ts_dist(ts)

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/offline/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts_raw = TimeSeries(in_path, "loss", dt_start, dt_end)

        plot_procedures.plot_ts_share_x(ts_raw, ts_dist, out_path,
                                        compress=True, title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0, 1.05, 0.05),
                                        title2="predicted: conf={}".
                                        format(conf))

if __name__ == "__main__":
    main()
