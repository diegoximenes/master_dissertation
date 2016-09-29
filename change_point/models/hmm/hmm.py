import os
import sys
import ghmm
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils
import change_point.models.change_point_alg as change_point_alg
import utils.time_series as time_series
from utils.time_series import TimeSeries

script_dir = os.path.join(os.path.dirname(__file__), ".")


class HMM(change_point_alg.ChangePointAlg):
    def get_seqs_set(self, obs_seqs):
        obs_seqs = self.get_obs_seqs(obs_seqs)
        obs_seqs_set = ghmm.SequenceSet(self.emission_domain, obs_seqs)
        return obs_seqs_set

    def baum_welch(self, obs_seqs):
        self.model = ghmm.HMMFromMatrices(self.emission_domain,
                                          self.emission_distr, self.A, self.B,
                                          self.pi)
        obs_seqs_set = self.get_seqs_set(obs_seqs)
        self.model.baumWelch(obs_seqs_set)

    def viterbi(self, ts):
        obs_seqs_set = self.get_seqs_set([ts.y])
        hidden_state_path = self.model.viterbi(obs_seqs_set)[0]
        ts_hidden_state_path = time_series.dist_ts(ts)
        for i in xrange(len(ts.x)):
            ts_hidden_state_path.x.append(ts.x[i])
            ts_hidden_state_path.y.append(hidden_state_path[i])
        return ts_hidden_state_path

    def xi(self, n, forward, backward, obs_t1, r, s, t):
        den = 0.0
        for i in xrange(n):
            for j in xrange(n):
                a_ij = self.model.getTransition(i, j)
                b_j_t1 = self.get_obs_lik(j, obs_t1)
                den += forward[t][i] * a_ij * b_j_t1 * backward[t + 1][j]
                print "i={}, j={}, aij={}, b_j_t1={}, obs_t1={}".format(i, j, a_ij,
                                                               b_j_t1, obs_t1)
        a_rs = self.model.getTransition(r, s)
        b_s_t1 = self.get_obs_lik(s, obs_t1)
        num = forward[t][r] * a_rs * b_s_t1 * backward[t + 1][r]
        print "num={}, den={}".format(num, den)
        return num / den

    def hidden_state_change_lik(self, ts):
        """
        obs.: compare distribution of different states. If they are too similar
        than they are merged during the probability computation
        """

        obs_seq = self.get_obs_seqs(ts.y)
        emission_seq = ghmm.EmissionSequence(self.emission_domain, obs_seq)

        # ALERT: I DON'T KNOW WHAT scale IS
        forward, scale = self.model.forward(emission_seq)
        backward = self.model.backward(emission_seq, scale)
        n = len(self.A)

        ts_hidden_state_change_lik = time_series.dist_ts(ts)
        for t in xrange(len(ts.y) - 1):
            lik = 0.0
            for i in xrange(n):
                for j in xrange(n):
                    if self.states_are_diff(i, j):
                        lik += self.xi(n, forward, backward, ts.y[t + 1], i, j,
                                       t)
                        lxi = self.xi(n, forward, backward, ts.y[t + 1], i, j,
                                      t)
                        print "i={}, j={}, t={}, xi={}".format(i, j, t, lxi)
            print "i={}, j={}, t={}, lik={}".format(i, j, t, lik)

            ts_hidden_state_change_lik.x.append(ts.x[t])
            ts_hidden_state_change_lik.y.append(lik)

        return ts_hidden_state_change_lik

    def print_model_to_file(self, out_path):
        with open(out_path, "w") as f:
            n = len(self.pi)

            # print states
            f.write("n={}\n".format(n))
            for i in xrange(n):
                pi = self.model.getInitial(i)
                f.write("state={}, distr={}, pi={:.5f}\n".
                        format(i, self.model.getEmission(i), pi))

            # print transitions
            for i in xrange(n):
                for j in xrange(n):
                    f.write("p({},{})={:.5f}\n".
                            format(str(i), str(j),
                                   self.model.getTransition(i, j)))

            # print initial point
            f.write("A={}\n".format(self.A))
            f.write("B={}\n".format(self.B))
            f.write("pi={}\n".format(self.pi))


class GaussianHMM(HMM):
    def __init__(self, preprocess_args, A, B, pi, thresh, min_peak_dist):
        self.preprocess_args = preprocess_args
        self.A = A
        self.B = B
        self.pi = pi
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
        print "mu={}, sigma={}".format(mu, sigma)
        lik = np.e ** (-(x - mu) ** 2 / (2 * sigma ** 2))
        print "lik1={}".format(lik)
        lik /= np.sqrt(2 * sigma ** 2 * np.pi)
        print "lik2={}".format(lik)
        return lik

    def states_are_diff(self, state1, state2):
        mu1, sigma2 = self.get_mu_sigma(state1)
        mu2, sigma2 = self.get_mu_sigma(state2)
        return (abs(mu1 - mu2) >= 0.01)

    def fit(self, df):
        pass

    def predict(self, row):
        ts = cp_utils.get_ts(row, self.preprocess_args)
        self.baum_welch([ts.y])


def create_dirs():
    for dir in ["{}/plots/".format(script_dir)]:
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
    param = {"A": A,
             "B": B,
             "pi": pi,
             "thresh": 0.5,
             "min_peak_dist": 10}

    hmm = GaussianHMM(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        pred = []
        # pred = hmm.predict(row)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        ts = cp_utils.get_ts(row, preprocess_args)
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        # print "pred={}".format(pred)
        # print "correct={}".format(correct)
        # print "conf={}".format(conf)

        hmm.baum_welch([ts.y])
        ts_hidden_state_path = hmm.viterbi(ts)
        ts_hidden_state_change_lik = hmm.hidden_state_change_lik(ts)
        hmm.print_model_to_file("./model.out")

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts_raw = TimeSeries(in_path, "loss", dt_start, dt_end)

        # hidden state path
        # plot_procedures.plot_ts_share_x(ts_raw, ts_hidden_state_path,
        #                                 out_path,
        #                                 compress=True, title1="correct",
        #                                 dt_axvline1=np.asarray(ts.x)[correct],
        #                                 dt_axvline2=np.asarray(ts.x)[pred],
        #                                 title2="predicted: conf={}".
        #                                 format(conf), plot_type2="scatter",
        #                                 ylim2=[-1, n])

        # hidden state change lik
        plot_procedures.plot_ts_share_x(ts_raw, ts_hidden_state_change_lik,
                                        out_path, compress=True,
                                        title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="predicted: conf={}".
                                        format(conf))
        return


if __name__ == "__main__":
    main()
