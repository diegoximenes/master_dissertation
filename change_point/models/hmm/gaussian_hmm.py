import os
import sys
import ghmm
import datetime
import numpy as np
from functools import partial

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils
import change_point.models.hmm.hmm as hmm
import change_point.models.change_point_alg as change_point_alg


class GaussianHMM(hmm.HMM):
    has_training = False

    def __init__(self, preprocess_args, metric, graph_structure_type, A, B, pi,
                 win_len, thresh, min_peak_dist):
        """
        Args:
            preprocess_args:
            metric:
            graph_structure_type: "predefined", "fully", "left_to_right"
            A: initial hidden states graph
            B: initial hidden states distribution
            pi: initial hidden states probabilities
            win_len: windows lengths of the sliding window offline
            thresh: in the peak detection, detect peaks that are greater than
                    thresh
            min_peak_dist: in the peak detection, detect peaks that are at
                           least separated by minimum peak distance

        """

        self.preprocess_args = preprocess_args
        self.metric = metric

        self.graph_structure_type = graph_structure_type
        self.A = A
        self.B = B
        self.pi = pi
        self.win_len = win_len
        self.thresh = thresh
        self.min_peak_dist = min_peak_dist

        self.emission_domain = ghmm.Float()
        self.emission_distr = ghmm.GaussianDistribution(self.emission_domain)

    def get_obs_seqs(self, seqs):
        return seqs

    def get_mu_sigma(self, state):
        emission = self.model.getEmission(state)
        mu, sigma = emission[0], emission[1]
        return mu, sigma

    def get_obs_lik(self, state, x):
        mu, sigma = self.get_mu_sigma(state)
        lik = np.e ** (-(x - mu) ** 2 / (2 * sigma ** 2))
        lik /= np.sqrt(2 * sigma ** 2 * np.pi)
        return lik

    def states_are_diff(self, state1, state2):
        mu1, sigma1 = self.get_mu_sigma(state1)
        mu2, sigma2 = self.get_mu_sigma(state2)
        return (abs(mu1 - mu2) >= 0.01)

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        hidden_state_y_ticks_labels = map(self.model.getEmission,
                                          range(len(self.A)))
        hidden_state_y_ticks_labels = map(lambda (mean, var):
                                          ("({:.3f}, {:.3f})".format(mean,
                                                                     var)),
                                          hidden_state_y_ticks_labels)
        self.plot_pipeline(ts, ts_raw, hidden_state_y_ticks_labels,
                           "(mean, variance)", correct, pred, conf, out_path)


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = GaussianHMM(preprocess_args=preprocess_args, metric=metric,
                        **param)

    utils.create_dirs(["{}/gaussian/".format(script_dir),
                       "{}/gaussian/plots/".format(script_dir),
                       "{}/gaussian/plots/{}".format(script_dir, dataset),
                       "{}/gaussian/plots/{}/{}".format(script_dir,
                                                        dataset, metric)])
    out_dir_path = "{}/gaussian/plots/{}/{}".format(script_dir, dataset,
                                                    metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    n = 4
    A = []
    for _ in xrange(n):
        A.append([1.0 / n] * n)
    B = [[0.0, 0.05], [0.05, 0.02], [0.15, 0.05], [0.5, 0.1]]
    pi = [1.0 / n] * n

    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}
    param = {"graph_structure_type": "predefined",
             "A": A,
             "B": B,
             "pi": pi,
             "win_len": 20,
             "thresh": 200,
             "min_peak_dist": 17}
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
