import os
import sys
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.utils.cp_utils as cp_utils
import change_point.utils.cmp_win as cmp_win
import change_point.models.change_point_alg as change_point_alg

script_dir = os.path.join(os.path.dirname(__file__), ".")


class SlidingWindowsOffline(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, win_len, thresh, min_peak_dist, f_dist,
                 bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
        """
        Args:
            preprocess_args:
            win_len: windows lengths of the sliding window offline
            thresh: in the peak detection, detect peaks that are greater than
                    thresh
            min_peak_dist: in the peak detection, detect peaks that are at
                           least separated by minimum peak distance
            f_dist = distance function between the windows
        """

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

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        ts_dist = self.get_ts_dist(ts)

        plot_procedures.plot_ts_share_x(ts_raw, ts_dist, out_path,
                                        compress=True, title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0, 1.05, 0.05),
                                        title2="predicted. conf={}".
                                        format(conf))


def create_dirs(dataset):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/{}/".format(script_dir, dataset),
                "{}/plots/{}/offline/".format(script_dir, dataset)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"win_len": 22,
             "thresh": 0.40232781537055823,
             "min_peak_dist": 12,
             "f_dist": cmp_win.hellinger_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}
    dataset = "rosam@land.ufrj.br"

    model = SlidingWindowsOffline(preprocess_args=preprocess_args, **param)

    create_dirs(dataset)
    out_dir_path = "{}/plots/{}/offline/".format(script_dir, dataset)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()
