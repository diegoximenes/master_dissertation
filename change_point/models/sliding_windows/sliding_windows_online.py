import os
import sys
import copy
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


class SlidingWindowsOnline(change_point_alg.ChangePointAlg):
    def __init__(self, preprocess_args, win_len, thresh, f_dist,
                 bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
        self.preprocess_args = preprocess_args
        self.win_len = win_len
        self.thresh = thresh
        self.f_dist = cp_utils.get_f_dist(f_dist, bin_size_f_dist,
                                          min_bin_f_dist, max_bin_f_dist)

    def slide(self, ts):
        ts_dist = time_series.dist_ts(ts)
        ts_dist.x = copy.deepcopy(ts.x)
        ts_dist.y = [None] * len(ts.y)

        cps = []
        i = 0
        while i + 2 * self.win_len - 1 < len(ts.y):
            win1 = ts.y[i:i + self.win_len]
            win2 = ts.y[i + self.win_len:i + 2 * self.win_len]
            dist = self.f_dist(win1, win2)

            ts_dist.y[i + self.win_len] = dist

            if dist > self.thresh:
                cps.append(i + self.win_len - 1)
                i += self.win_len
            else:
                i += 1
        return cps, ts_dist

    def fit(self, df):
        pass

    def predict(self, ts):
        cps, _ = self.slide(ts)
        return cps


def create_dirs():
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/online/".format(script_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"win_len": 20,
             "thresh": 0.1,
             "f_dist": cmp_win.mean_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}

    sliding_windows = SlidingWindowsOnline(preprocess_args=preprocess_args,
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

        _, ts_dist = sliding_windows.slide(ts)

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/online/server{}_mac{}_dtstart{}_dtend{}.png".
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
