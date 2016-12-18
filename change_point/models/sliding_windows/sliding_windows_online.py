import os
import sys
import copy
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
        plot_procedures.plot_ts_share_x(ts, ts_dist, out_path,
                                        compress=True,
                                        title1="median filtered",
                                        title2="mean distance sliding windows",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        xlabel="$i$",
                                        ylabel2="$D_{i}$ (ms)",
                                        ylabel1="latency (ms)")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = SlidingWindowsOnline(preprocess_args=preprocess_args,
                                 metric=metric, **param)

    utils.create_dirs(["{}/online/".format(script_dir),
                       "{}/online/plots/".format(script_dir),
                       "{}/online/plots/{}".format(script_dir, dataset),
                       "{}/online/plots/{}/{}".format(script_dir, dataset,
                                                      metric)])
    out_dir_path = "{}/online/plots/{}/{}".format(script_dir, dataset,
                                                  metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    # only used if RUN_MODE == specific_client
    server = "NHODTCSRV04"
    mac = "64:66:B3:A6:B3:22"
    # only used if RUN_MODE == specific_client or RUN_MODE == single
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    # used in all RUN_MODE
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}
    param = {"win_len": 20,
             "thresh": 15,
             "f_dist": cmp_win.mean_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}
    metric = "latency"

    parallel_args = {"cmp_class_args": cmp_class_args,
                     "preprocess_args": preprocess_args, "param": param,
                     "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    specific_client_args = single_args
    fp_specific_client = partial(change_point_alg.run_specific_client,
                                 mac=mac, server=server,
                                 model_class=SlidingWindowsOnline,
                                 out_path=script_dir)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args,
                        fp_specific_client,
                        specific_client_args)
