import os
import sys
import datetime
import numpy as np
from functools import partial
# import matplotlib.cm as cm
# import matplotlib.pylab as plt

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.time_series as time_series
import change_point.cp_utils.cp_utils as cp_utils
import change_point.models.change_point_alg as change_point_alg
import bayesian_changepoint_detection.online_changepoint_detection as oncd


class BayesianOnline(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, hazard_lambda, future_win_len,
                 thresh, min_peak_dist):
        """
        Args:
            preprocess_args:
            metric:
            hazard_lambda: prior on p(current run lenght | last run length)
            future_win_len: to decide if t is a change point, it is considered
                            the [0:t + future_win_len] interval
            thresh: in the peak detection, detect peaks that are greater than
                    thresh
            min_peak_dist: in the peak detection, detect peaks that are at
                           least separated by minimum peak distance
        """

        self.preprocess_args = preprocess_args
        self.metric = metric

        self.hazard_lambda = hazard_lambda
        self.future_win_len = future_win_len
        self.thresh = thresh
        self.min_peak_dist = min_peak_dist

    def get_cp_prob(self, ts):
        f_hazard = partial(oncd.constant_hazard, self.hazard_lambda)
        prob_length, map_estimates = oncd.online_changepoint_detection(
            np.asarray(ts.y), f_hazard, oncd.StudentT(0.1, .01, 1, 0))

        if ((prob_length.shape[0] >= self.future_win_len) and
                (prob_length.shape[1] >= self.future_win_len)):
            cp_prob = prob_length[self.future_win_len, self.future_win_len:-1]
        else:
            cp_prob = []

        # fig, ax = plt.subplots(figsize=[18, 16])
        # ax = fig.add_subplot(3, 1, 1)
        # ax.scatter(range(len(ts.y)), ts.y)
        # ax = fig.add_subplot(3, 1, 2, sharex=ax)
        # sparsity = 5  # only plot every fifth data for faster display
        # ax.pcolor(np.array(range(0, len(prob_length[:, 0]), sparsity)),
        #           np.array(range(0, len(prob_length[:, 0]), sparsity)),
        #           -np.log(prob_length[0:-1:sparsity, 0:-1:sparsity]),
        #           cmap=cm.Greys, vmin=0, vmax=30)
        # ax = fig.add_subplot(3, 1, 3, sharex=ax)
        # ax.plot(prob_length[self.future_win_len,
        #                     self.future_win_len:-1])
        # plt.show()

        if len(cp_prob):
            cp_prob[0] = 0.0
        ts_cp_prob = time_series.dist_ts(ts)
        for i in xrange(len(cp_prob) - 1):
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
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="probabilities",
                                        ylabel1=ylabel1,
                                        ylabel2="p($i$ is change point)",
                                        xlabel="$i$")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = BayesianOnline(preprocess_args=preprocess_args, metric=metric,
                           **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/online/".format(script_dir, dataset),
                       "{}/plots/{}/online/{}".format(script_dir, dataset,
                                                      metric)])
    out_dir_path = "{}/plots/{}/online/{}".format(script_dir, dataset,
                                                  metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    # only used if RUN_MODE == specific_client
    server = "POADTCSRV04"
    mac = "64:66:B3:A6:BB:3A"
    # only used if RUN_MODE == specific_client or RUN_MODE == single
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    # used in all RUN_MODE
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"win_len": 5,
                       "filter_type": "percentile_filter",
                       "p": 0.5}
    param = {"hazard_lambda": 24.60864360138786,
             "future_win_len": 10,
             "thresh": 0.6,
             "min_peak_dist": 11}
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
                                 model_class=BayesianOnline,
                                 out_path=script_dir)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args,
                        fp_specific_client,
                        specific_client_args)
