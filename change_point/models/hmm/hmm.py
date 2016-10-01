import os
import sys
import ghmm

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import change_point.utils.cmp_win as cmp_win
import change_point.models.change_point_alg as change_point_alg
from change_point.models.sliding_windows.sliding_windows_offline import \
    SlidingWindowsOffline
import utils.time_series as time_series

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

    # TODO: this method is numerically unstable
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

    def viterbi_sliding_windows_pipeline(self, ts):
        self.baum_welch([ts.y])
        ts_hidden_state_path = self.viterbi(ts)

        n = len(self.A)
        preprocess_args = {"filter_type": "none"}
        param = {"win_len": self.win_len,
                 "thresh": self.thresh,
                 "min_peak_dist": self.min_peak_dist,
                 "f_dist": cmp_win.hellinger_dist,
                 "bin_size_f_dist": 1,
                 "min_bin_f_dist": 0,
                 "max_bin_f_dist": n - 1}
        sliding_windows = \
            SlidingWindowsOffline(preprocess_args=preprocess_args, **param)
        pred = sliding_windows.predict(ts_hidden_state_path)
        ts_sliding_windows_dist = \
            sliding_windows.get_ts_dist(ts_hidden_state_path)

        return pred, ts_hidden_state_path, ts_sliding_windows_dist

    def fit(self, df):
        pass

    def predict(self, ts):
        pred, _, _ = self.viterbi_sliding_windows_pipeline(ts)
        return pred
