import os
import sys
import pandas as pd

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cmp_win as cmp_win

script_dir = os.path.join(os.path.dirname(__file__), ".")


class SlidingWindows():
    def __init__(self, preprocess_args, win_len, f_dist):
        self.preprocess_args = preprocess_args
        self.win_len = win_len
        self.f_dist = f_dist

    def get_dist_ts(self, ts):
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

    def predict(self, row):
        pass

    def score(self, df, cmp_class_args):
        pass


def create_dirs():
    for dir in ["{}/plots/".format(script_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    preprocess_args = {"filter_type": "none"}
    param = {"win_len": 10,
             "f_dist": cmp_win.mean_dist}

    sliding_windows = SlidingWindows(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    for idx, row in df.iterrows():
        print "row={}".format(row)

        ts = cmp_class.get_ts(row, preprocess_args)
        ts_dist = sliding_windows.get_dist_ts(ts)

        _, dt_start, dt_end = cmp_class.unpack_pandas_row(row)
        out_path = ("{}/plots/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))

        plot_procedures.plot_ts_share_x(ts, ts_dist, out_path, compress=True)

if __name__ == "__main__":
    main()
