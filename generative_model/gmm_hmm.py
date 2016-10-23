import os
import sys
import numpy as np
import hmmlearn.hmm
import sklearn.mixture

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
from generative_model.hmm import HMM


class GMMHMM(HMM):
    def __init__(self, a, pi, weight, mean, covar):
        self.model = hmmlearn.hmm.GMMHMM(n_components=len(pi),
                                         n_mix=len(weight[0]),
                                         init_params="")
        self.model.transmat_ = np.array(a)
        self.model.startprob_ = np.array(pi)
        self.model.gmms_ = []
        for i in xrange(len(weight)):
            gmm = sklearn.mixture.GMM(n_components=len(weight[i]),
                                      init_params="")
            gmm.weights_ = np.array(weight[i])
            gmm.means_ = np.array(mean[i])
            gmm.covars_ = np.array(covar[i])
            self.model.gmms_.append(gmm)

    def write_states(self, f):
        for i in xrange(self.model.n_components):
            for j in xrange(self.model.gmms_[i].n_components):
                f.write("state={}, gaussian_id={}, weight={}, mean={},"
                        " covar={}\n".
                        format(i, j, self.model.gmms_[i].weights_[j],
                               self.model.gmms_[i].means_[j],
                               self.model.gmms_[i].covars_[j]))


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
    # weight[i][j] weight of gaussian j of state i
    weight = [[0.9, 0.1], [0.6, 0.4], [0.9, 0.1], [0.5, 0.5], [0.5, 0.5]]
    # mean = hidden states means. mean[i][j][0] = mean of feature 0 of gaussian
    # j of state i
    mean = [[[0.0], [0.01]], [[0.04], [0.06]], [[0.1], [0.2]], [[0.5], [0.6]],
            [[0.8], [0.9]]]
    # covar = hidden states covariance. covar[i][j][0] = variance feature 0 of
    # gaussian j of state i
    covar = [[[0.01], [0.01]], [[0.02], [0.02]], [[0.05], [0.05]],
             [[0.05], [0.05]], [[0.05], [0.05]]]

    hmm = GMMHMM(a, pi, weight, mean, covar)
    hmm.run()
