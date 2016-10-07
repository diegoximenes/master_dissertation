import os
import sys
import ghmm

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import change_point.utils.cmp_win as cmp_win
import change_point.models.hmm.hmm as hmm

script_dir = os.path.join(os.path.dirname(__file__), ".")


class DiscreteHMM(hmm.HMM):
    has_training = False

    def __init__(self, preprocess_args, graph_structure_type, A, B, pi,
                 obs_bins, win_len, thresh, min_peak_dist):
        """
        Args:
            preprocess_args:
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


def create_dirs(dataset):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/{}/".format(script_dir, dataset),
                "{}/plots/{}/discrete/".format(script_dir, dataset)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
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
    dataset = "rosam@land.ufrj.br"

    model = DiscreteHMM(preprocess_args=preprocess_args, **param)

    create_dirs(dataset)
    out_dir_path = "{}/plots/{}/discrete/".format(script_dir, dataset)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()
