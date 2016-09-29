import os
import sys
import ghmm
import pandas as pd
import numpy as np
from functools import partial

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cmp_win as cmp_win
import change_point.utils.cp_utils as cp_utils
import change_point.models.change_point_alg as change_point_alg
from change_point.models.sliding_windows.sliding_windows_offline import \
    SlidingWindowsOffline
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
        self.st_st = self.merge_states()

    def merge_states(self):
        """
        if two states are too similar then they are merged

        returns a dictionary that maps a state to a state.
        dic[st] indicates that state dic[st] should replaced by st
        """
        dic = {}
        n = len(self.A)
        for i in xrange(n):
            dic[i] = i
            for j in xrange(i):
                if not self.states_are_diff(i, j):
                    dic[i] = j
                    break
        return dic

    def viterbi(self, ts):
        obs_seqs_set = self.get_seqs_set([ts.y])
        hidden_state_path = self.model.viterbi(obs_seqs_set)[0]
        ts_hidden_state_path = time_series.dist_ts(ts)
        for i in xrange(len(ts.x)):
            ts_hidden_state_path.x.append(ts.x[i])
            ts_hidden_state_path.y.append(self.st_st[hidden_state_path[i]])
        return ts_hidden_state_path

    # TODO: this method  is numerically unstable
    def xi(self, n, forward, backward, obs_t1, r, s, t):
        den = 0.0
        for i in xrange(n):
            for j in xrange(n):
                a_ij = self.model.getTransition(i, j)
                b_j_t1 = self.get_obs_lik(j, obs_t1)
                den += forward[t][i] * a_ij * b_j_t1 * backward[t + 1][j]
        a_rs = self.model.getTransition(r, s)
        b_s_t1 = self.get_obs_lik(s, obs_t1)
        num = forward[t][r] * a_rs * b_s_t1 * backward[t + 1][r]
        return num / den

    # TODO: this method is numerically unstable
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

    def fit(self, df):
        pass

    def predict(self, ts):
        self.baum_welch([ts.y])
        ts_hidden_state_path = self.viterbi(ts)

        n = len(self.A)
        preprocess_args = {"filter_type": "none"}
        param = {"win_len": self.win_len,
                 "thresh": self.thresh,
                 "min_peak_dist": self.min_peak_dist,
                 "f_dist": partial(cmp_win.hmm_win_dist, n=n),
                 "bin_size_f_dist": None}
        sliding_windows = \
            SlidingWindowsOffline(preprocess_args=preprocess_args, **param)
        pred = sliding_windows.predict(ts_hidden_state_path)

        return pred


class GaussianHMM(HMM):
    def __init__(self, preprocess_args, A, B, pi, win_len, thresh,
                 min_peak_dist):
        self.preprocess_args = preprocess_args
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
             "win_len": 10,
             "thresh": 0.7,
             "min_peak_dist": 10}

    hmm = GaussianHMM(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        ts = cp_utils.get_ts(row, preprocess_args)
        pred = hmm.predict(ts)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        hmm.baum_welch([ts.y])
        ts_hidden_state_path = hmm.viterbi(ts)
        # ts_hidden_state_change_lik = hmm.hidden_state_change_lik(ts)
        # hmm.print_model_to_file("./model.out")

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts_raw = TimeSeries(in_path, "loss", dt_start, dt_end)

        # hidden state path
        plot_procedures.plot_ts_share_x(ts_raw, ts_hidden_state_path,
                                        out_path,
                                        compress=True, title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="predicted: conf={}".
                                        format(conf), plot_type2="scatter",
                                        ylim2=[-1, n])

        # hidden state change lik
        # plot_procedures.plot_ts_share_x(ts_raw, ts_hidden_state_change_lik,
        #                                 out_path, compress=True,
        #                                 title1="correct",
        #                                 dt_axvline1=np.asarray(ts.x)[correct],
        #                                 dt_axvline2=np.asarray(ts.x)[pred],
        #                                 title2="predicted: conf={}".
        #                                 format(conf))
        # return


if __name__ == "__main__":
    main()
