import os
import sys
import ghmm
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import change_point.models.hmm.hmm as hmm

script_dir = os.path.join(os.path.dirname(__file__), ".")


class GaussianHMM(hmm.HMM):
    has_training = False

    def __init__(self, preprocess_args, graph_structure_type, A, B, pi,
                 win_len, thresh, min_peak_dist):
        """
        Args:
            preprocess_args:
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


def create_dirs(dataset):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/{}/".format(script_dir, dataset),
                "{}/plots/{}/gaussian/".format(script_dir, dataset)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    n = 4
    A = []
    for _ in xrange(n):
        A.append([1.0 / n] * n)
    B = [[0.0, 0.05], [0.05, 0.02], [0.15, 0.05], [0.5, 0.1]]
    pi = [1.0 / n] * n

    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "none"}
    param = {"graph_structure_type": "predefined",
             "A": A,
             "B": B,
             "pi": pi,
             "win_len": 27,
             "thresh": 0.32266574449686963,
             "min_peak_dist": 17}
    dataset = "rosam@land.ufrj.br"

    model = GaussianHMM(preprocess_args=preprocess_args, **param)

    create_dirs(dataset)
    out_dir_path = "{}/plots/{}/gaussian/".format(script_dir, dataset)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()