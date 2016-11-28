import os
import sys
import numpy as np
import hmmlearn.hmm

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import change_point.cp_utils.cmp_win as cmp_win
from generative_model.hmm import HMM


class DiscreteHMM(HMM):
    def __init__(self, a, pi, obs_bins, b):
        self.model = hmmlearn.hmm.MultinomialHMM(n_components=len(pi),
                                                 init_params="")
        self.model.transmat_ = np.array(a)
        self.model.startprob_ = np.array(pi)
        self.model.emissionprob_ = np.array(b)
        self.obs_bins = obs_bins

    def get_seq(self, ts):
        seq = []
        for y in ts.y:
            seq.append([cmp_win.get_bin(y, self.obs_bins)])
        return seq

    def write_states(self, f):
        for i in xrange(self.model.n_components):
            for j in xrange(len(self.model.emissionprob_[i])):
                if j == 0:
                    symbol_interval = "[0, {}]".format(obs_bins[j])
                else:
                    symbol_interval = "({}, {}]".format(obs_bins[j - 1],
                                                        obs_bins[j])
                f.write("state={}, symbol={}, symbol_interval={}, prob={}\n".
                        format(i, j, symbol_interval,
                               self.model.emissionprob_[i][j]))

if __name__ == "__main__":
    # these variables defines the initial point of the HMM
    # a == hidden states transitions matrix. a[i][j] == probability of
    # transition from state i to j
    a = [[0.8, 0.2, 0.0, 0.0, 0.0],
         [0.1, 0.8, 0.1, 0.0, 0.0],
         [0.0, 0.1, 0.8, 0.1, 0.0],
         [0.0, 0.0, 0.1, 0.8, 0.1],
         [0.0, 0.0, 0.0, 0.2, 0.8]]
    # pi == hidden states start likelihood. pi[i] probability of starting
    # sequence in state i
    pi = [0.2, 0.2, 0.2, 0.2, 0.2]
    # obs_bins defines the symbols: symbol 0 represents observations in
    # [0, obs_bins[0]], symbol 1 represents observations in
    # (obs_bins[0], obs_bins[1]]
    obs_bins = [0.01, 0.05, 0.1, 0.3, 1.0]
    # b[i][j] == probability of emission of symbol j in state i
    b = [[0.9, 0.1, 0.0, 0.0, 0.0],
         [0.1, 0.7, 0.1, 0.0, 0.1],
         [0.2, 0.2, 0.5, 0.1, 0.0],
         [0.1, 0.1, 0.4, 0.3, 0.1],
         [0.0, 0.0, 0.2, 0.3, 0.5]]

    hmm = DiscreteHMM(a, pi, obs_bins, b)
    hmm.run()
