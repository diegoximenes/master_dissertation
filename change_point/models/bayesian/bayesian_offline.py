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
import change_point.models.change_point_alg as change_point_alg
import bayesian_changepoint_detection.offline_changepoint_detection as offcd


class BayesianOffline(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, prior, p, k, thresh,
                 min_peak_dist):
        self.preprocess_args = preprocess_args
        self.metric = metric

        self.prior = prior
        self.p = p
        self.k = k
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

        # ALERT: the truncate parameter can affect the performance
        q, p, pcp = offcd.offline_changepoint_detection(
            l, prior, offcd.gaussian_obs_log_likelihood, truncate=-90)
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

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        ts_cp_prob = self.get_cp_prob(ts)

        ylabel1 = plot_procedures.get_default_ylabel(ts)
        plot_procedures.plot_ts_share_x(ts, ts_cp_prob, out_path,
                                        compress=True,
                                        title1="median filtered",
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0.0, 1.0 + 0.1, 0.1),
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        y_axhline2=[self.thresh],
                                        title2="probabilities",
                                        ylabel1=ylabel1,
                                        ylabel2="p($i$ is change point)",
                                        xlabel="$i$")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = BayesianOffline(preprocess_args=preprocess_args, metric=metric,
                            **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/offline/".format(script_dir, dataset),
                       "{}/plots/{}/offline/{}".format(script_dir, dataset,
                                                       metric)])
    out_dir_path = "{}/plots/{}/offline/{}".format(script_dir, dataset,
                                                   metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    # only used if RUN_MODE == specific_client
    server = "SNEDTCPROB01"
    mac = "64:66:B3:A6:BB:80"
    # only used if RUN_MODE == specific_client or RUN_MODE == single
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    # used in all RUN_MODE
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"win_len": 5,
                       "filter_type":
                       "percentile_filter",
                       "p": 0.5}
    param = {"prior": offcd.const_prior,
             "p": 0.8,
             "k": 20,
             "thresh": 0.6,
             "min_peak_dist": 10}
    metric = "loss"

    parallel_args = {"cmp_class_args": cmp_class_args,
                     "preprocess_args": preprocess_args, "param": param,
                     "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    specific_client_args = single_args
    fp_specific_client = partial(change_point_alg.run_specific_client,
                                 mac=mac, server=server,
                                 model_class=BayesianOffline,
                                 out_path=script_dir)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args,
                        fp_specific_client,
                        specific_client_args)
