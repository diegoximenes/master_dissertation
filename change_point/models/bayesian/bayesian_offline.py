import os
import sys
import pandas as pd
import numpy as np
from functools import partial

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils
import change_point.models.change_point_alg as change_point_alg
from utils.time_series import TimeSeries
import bayesian_changepoint_detection.offline_changepoint_detection as offcd

script_dir = os.path.join(os.path.dirname(__file__), ".")


class BayesianOffline(change_point_alg.ChangePointAlg):
    def __init__(self, preprocess_args, prior, p, k, thresh, min_peak_dist):
        self.prior = prior
        self.p = p
        self.k = k
        self.preprocess_args = preprocess_args
        self.thresh = thresh
        self.min_peak_dist = min_peak_dist

    def get_prior(self, prior, p, k, l):
        if prior == offcd.const_prior:
            return partial(prior, l=l)
        elif prior == offcd.geometric_prior:
            return partial(prior, p=p)
        elif prior == offcd.neg_binominal_prior:
            return partial(prior, k=k, p=p)

    def get_cp_prob(self, ts):
        l = np.asarray(ts.y)
        prior = self.get_prior(self.prior, self.p, self.k, len(l) + 1)

        q, p, pcp = offcd.offline_changepoint_detection(
            l, prior, offcd.gaussian_obs_log_likelihood, truncate=-40)
        cp_prob = np.exp(pcp).sum(0)

        ts_cp_prob = time_series.dist_ts(ts)
        for i in xrange(len(ts.x) - 1):
            ts_cp_prob.x.append(ts.x[i])
            ts_cp_prob.y.append(cp_prob[i])
        return ts_cp_prob

    def fit(self, df):
        pass

    def predict(self, ts):
        ts_cp_prob = self.get_cp_prob(ts)
        cp_prob_peaks = cp_utils.detect_peaks(ts_cp_prob.y, mph=self.thresh,
                                              mpd=self.min_peak_dist)
        return cp_prob_peaks


def create_dirs():
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/offline/".format(script_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"prior": offcd.geometric_prior,
             "p": 0.1,
             "k": 10,
             "thresh": 0.1,
             "min_peak_dist": 10}

    bayesian = BayesianOffline(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        ts = cp_utils.get_ts(row, preprocess_args)
        pred = bayesian.predict(ts)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/offline/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts_raw = TimeSeries(in_path, "loss", dt_start, dt_end)

        ts_cp_prob = bayesian.get_cp_prob(ts)

        plot_procedures.plot_ts_share_x(ts_raw, ts_cp_prob, out_path,
                                        compress=True, title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0, 1.05, 0.05),
                                        title2="predicted: conf={}".
                                        format(conf))

if __name__ == "__main__":
    main()
