# TODO: change to hmmlearn

import os
import sys
import datetime
import ghmm
from functools import partial

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cmp_win as cmp_win
import change_point.cp_utils.cp_utils as cp_utils
import change_point.models.hmm.hmm as hmm
import change_point.models.change_point_alg as change_point_alg


class DiscreteHMM(hmm.HMM):
    has_training = False

    def __init__(self, preprocess_args, metric, graph_structure_type, A, B, pi,
                 obs_bins, win_len, thresh, min_peak_dist):
        """
        Args:
            preprocess_args:
            metric:
            graph_structure_type: "predefined", "fully", "left_to_right"
            A: initial hidden states graph
            B: initial hidden states distribution
            pi: initial hidden states probabilities
            obs_bins: bins used in the hidden states distribution
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
        self.obs_bins = obs_bins
        self.win_len = win_len
        self.thresh = thresh
        self.min_peak_dist = min_peak_dist

        m = len(self.B[0])  # num of symbols
        self.emission_domain = ghmm.IntegerRange(0, m)
        self.emission_distr = ghmm.DiscreteDistribution(self.emission_domain)

    def get_obs_seqs(self, seqs):
        """
        transform seqs in bin_seqs
        """

        bin_seqs = []
        for seq in seqs:
            bin_seq = []
            for x in seq:
                bin_seq.append(cmp_win.get_bin(x, self.obs_bins))
            bin_seqs.append(bin_seq)
        return bin_seqs

    # TODO
    def get_obs_lik(self, state, x):
        return 1.0

    def states_are_diff(self, state1, state2):
        distr1 = self.model.getEmission(state1)
        distr2 = self.model.getEmission(state2)
        for i in xrange(len(distr1)):
            if abs(distr1[i] - distr2[i]) >= 0.01:
                return True
        return False

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        # write states distribution to a file
        hidden_state_y_ticks_labels = map(self.model.getEmission,
                                          range(len(self.A)))
        with open("{}_states.txt".format(out_path), "w") as f:
            f.write("state,distr\n")
            for i in xrange(len(hidden_state_y_ticks_labels)):
                f.write("{},{}\n".format(i, hidden_state_y_ticks_labels[i]))

        self.plot_pipeline(ts, ts_raw, range(len(self.A)), "", correct, pred,
                           conf, out_path)


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = DiscreteHMM(preprocess_args=preprocess_args, metric=metric,
                        **param)

    utils.create_dirs(["{}/discrete/".format(script_dir),
                       "{}/discrete/plots/".format(script_dir),
                       "{}/discrete/plots/{}".format(script_dir, dataset),
                       "{}/discrete/plots/{}/{}".format(script_dir,
                                                        dataset, metric)])
    out_dir_path = "{}/discrete/plots/{}/{}".format(script_dir, dataset,
                                                    metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    n = 4
    A = []
    for _ in xrange(n):
        A.append([1.0 / n] * n)
    B = [[0.9, 0.1, 0.0, 0.0, 0.0],
         [0.1, 0.7, 0.1, 0.0, 0.1],
         [0.2, 0.2, 0.5, 0.1, 0.0],
         [0.1, 0.1, 0.4, 0.3, 0.1]]
    pi = [1.0 / n] * n
    obs_bins = [0.01, 0.05, 0.1, 0.3, 1.0]

    # only used if RUN_MODE == specific_client
    server = "POADTCSRV04"
    mac = "64:66:B3:A6:BB:3A"
    # only used if RUN_MODE == specific_client or RUN_MODE == single
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 7, 11)
    # used in all RUN_MODE
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"graph_structure_type": "predefined",
             "A": A,
             "B": B,
             "pi": pi,
             "obs_bins": obs_bins,
             "win_len": 9,
             "thresh": 0.5001054151917693,
             "min_peak_dist": 7}
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
                                 model_class=DiscreteHMM,
                                 out_path=script_dir)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args,
                        fp_specific_client,
                        specific_client_args)
