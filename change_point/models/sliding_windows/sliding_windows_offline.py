import os
import sys
import datetime
import numpy as np
from functools import partial

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.cp_utils.cp_utils as cp_utils
import change_point.cp_utils.cmp_win as cmp_win
import change_point.models.change_point_alg as change_point_alg


class SlidingWindowsOffline(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, win_len, thresh, min_peak_dist,
                 f_dist, bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
        """
        Args:
            preprocess_args:
            metric:
            win_len: windows lengths of the sliding window offline
            thresh: in the peak detection, detect peaks that are greater than
                    thresh
            min_peak_dist: in the peak detection, detect peaks that are at
                           least separated by minimum peak distance
            f_dist = distance function between the windows
        """

        self.preprocess_args = preprocess_args
        self.metric = metric

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

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        ts_dist = self.get_ts_dist(ts)

        plot_procedures.plot_ts_share_x(ts, ts_dist, out_path,
                                        compress=True,
                                        title1="median filtered",
                                        title2="sliding windows distance",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        xlabel="$i$",
                                        ylabel2="$D_{i}$ (ms)",
                                        ylabel1="latency (ms)")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = SlidingWindowsOffline(preprocess_args=preprocess_args,
                                  metric=metric, **param)

    utils.create_dirs(["{}/offline/".format(script_dir),
                       "{}/offline/plots/".format(script_dir),
                       "{}/offline/plots/{}/".format(script_dir, dataset),
                       "{}/offline/plots/{}/{}".format(script_dir, dataset,
                                                       metric)])
    out_dir_path = "{}/offline/plots/{}/{}".format(script_dir, dataset,
                                                   metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}
    param = {"win_len": 20,
             "thresh": 100,
             "min_peak_dist": 18,
             "f_dist": cmp_win.mean_dist,
             "bin_size_f_dist": 5,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 200}
    metric = "latency"

    parallel_args = {"cmp_class_args": cmp_class_args,
                     "preprocess_args": preprocess_args, "param": param,
                     "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args)
