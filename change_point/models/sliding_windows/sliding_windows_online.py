import os
import sys
import copy
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.utils.cp_utils as cp_utils
import change_point.utils.cmp_win as cmp_win
import change_point.models.change_point_alg as change_point_alg


class SlidingWindowsOnline(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, win_len, thresh, f_dist,
                 bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
        """
        Args:
            preprocess_args:
            metric:
            win_len: windows lengths of the sliding window offline
            thresh: threshold used to detect change points
            f_dist = distance function between the windows
        """

        self.preprocess_args = preprocess_args
        self.metric = metric

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

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        _, ts_dist = self.slide(ts)
        plot_procedures.plot_ts_share_x(ts_raw, ts_dist, out_path,
                                        compress=True, title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="predicted. conf={}".
                                        format(conf))


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"win_len": 30,
             "thresh": 0.3381211781368245,
             "f_dist": cmp_win.hellinger_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}
    metric = "loss"
    dataset = "rosam@land.ufrj.br"

    model = SlidingWindowsOnline(preprocess_args=preprocess_args,
                                 metric=metric, **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/online/".format(script_dir, dataset),
                       "{}/plots/{}/online/{}".format(script_dir, dataset,
                                                      metric)])
    out_dir_path = "{}/plots/{}/online/{}".format(script_dir, dataset, metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()
