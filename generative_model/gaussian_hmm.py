import os
import sys
import numpy as np
import hmmlearn.hmm

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
from generative_model.hmm import HMM


class GaussianHMM(HMM):
    def __init__(self, a, pi, mean, covar):
        self.model = hmmlearn.hmm.GaussianHMM(n_components=len(pi),
                                              init_params="")
        self.model.transmat_ = np.array(a)
        self.model.startprob_ = np.array(pi)
        self.model.means_ = np.array(mean)
        self.model.covars_ = np.array(covar)

    def write_states(self, f):
        for i in xrange(self.model.n_components):
            f.write("state={}, mean={}, covar={}\n".
                    format(i, self.model.means_[i], self.model.covars_[i]))


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
    pi = [1.0, 0.0, 0.0, 0.0, 0.0]
    # mean = hidden states means. mean[i][0] = mean of feature 0 of state i
    mean = [[0.01], [0.03], [0.07], [0.1], [0.3]]
    # covar = hidden states covariance. covar[i][0] = variance feature 0 of
    # state i
    covar = [[0.01], [0.01], [0.03], [0.03], [0.1]]

    hmm = GaussianHMM(a, pi, mean, covar)
    hmm.run()
