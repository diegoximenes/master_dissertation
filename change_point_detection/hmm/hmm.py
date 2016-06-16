"""
ALERT: left right discrete HMM suffer from silent states.
Example: pi = [1, 0], A = [[0.5, 0.5], [0, 1]], B = [[1, 0], [0, 1]],
obs = [1, 1]. The HMM always start in the state 0 which have zero
probability of observing the first observation of obs.
"""

import ghmm
import os
import sys
import copy
import datetime

sys.path.append("../../import_scripts/")
import time_series
import plot_procedures
from time_series import TimeSeries

# PARAMETERS
metric = "loss"

# HMM PARAMETERS
# full gauss
n_full_gauss = 4
A_full_gauss = []
for _ in xrange(n_full_gauss):
    A_full_gauss.append([1.0 / n_full_gauss] * n_full_gauss)
B_full_gauss = [[0.0, 0.05], [0.02, 0.02], [0.04, 0.4], [0.1, 2]]
pi_full_gauss = [1.0 / n_full_gauss] * n_full_gauss

# left right gauss
n_left_right_gauss = 5
A_left_right_gauss = [[0.5, 0.5, 0, 0, 0], [0, 0.5, 0.5, 0, 0],
                      [0, 0, 0.5, 0.5, 0], [0, 0, 0, 0.5, 0.5],
                      [0, 0, 0, 0, 1.0]]
B_left_right_gauss = [[0.0, 0.05], [0.1, 0.1], [0.5, 0.1], [0.8, 0.1],
                      [0.25, 0.1]]
pi_left_right_gauss = [1.0, 0, 0, 0, 0]

# full discr
n_full_discr = 4
A_full_discr = []
for _ in xrange(n_full_discr):
    A_full_discr.append([1.0 / n_full_discr] * n_full_discr)
B_full_discr = [[0.9, 0.1, 0.0, 0.0], [0.1, 0.7, 0.1, 0.1],
                [0.2, 0.2, 0.5, 0.1], [0.1, 0.1, 0.4, 0.4]]
pi_full_discr = [1.0 / n_full_discr] * n_full_discr

# left right discr
n_left_right_discr = 5
A_left_right_discr = [[0.5, 0.5, 0, 0, 0], [0, 0.5, 0.5, 0, 0],
                      [0, 0, 0.5, 0.5, 0], [0, 0, 0, 0.5, 0.5],
                      [0, 0, 0, 0, 1.0]]
B_left_right_discr = [[0.9, 0.1, 0.0, 0.0], [0.1, 0.7, 0.1, 0.1],
                      [0.2, 0.2, 0.5, 0.1], [0.1, 0.1, 0.4, 0.4],
                      [0.25, 0.25, 0.25, 0.25]]
pi_left_right_discr = [1.0, 0, 0, 0, 0]


class HMM():

    def __init__(self):
        self.model = None
        self.emission_domain = None
        self.emission_distr = None

        # initial parameters
        self.A = None
        self.B = None
        self.pi = None

    def train(self, A, B, pi, seqs, out_path=None):
        # save initial point
        self.A = copy.deepcopy(A)
        self.B = copy.deepcopy(B)
        self.pi = copy.deepcopy(pi)

        self.set_emission()

        seqs = self.get_obs_seqs(seqs)

        obs_seqs = ghmm.SequenceSet(self.emission_domain, seqs)

        self.model = ghmm.HMMFromMatrices(self.emission_domain,
                                          self.emission_distr, A, B, pi)
        self.model.baumWelch(obs_seqs)

        if out_path is not None:
            self.print_model_to_file("{}.txt".format(out_path))

    def viterbi(self, ts, out_path):
        seq = self.get_obs_seqs([ts.raw_y])
        obs_seq = ghmm.SequenceSet(self.emission_domain, seq)

        hidden_state_path = self.model.viterbi(obs_seq)[0]

        # plot
        if out_path is not None:
            ts_dist = time_series.dist_ts(ts)
            for i in xrange(len(ts.raw_x)):
                dt = ts.raw_x[i]
                ts_dist.raw_x.append(dt)
                ts_dist.raw_y.append(hidden_state_path[i])
                ts_dist.x.append(dt)
                ts_dist.y.append(hidden_state_path[i])

            n = len(self.pi)
            hidden_state_ticks = range(n)
            hidden_state_tick_labels = []
            for i in xrange(n):
                state_distr = self.model.getEmission(i)
                tick_labels = "{:.2f}" + ",{:.2f}" * (len(state_distr) - 1)
                hidden_state_tick_labels.append(tick_labels.
                                                format(*state_distr))

            plot_procedures.plot_ts_and_dist(ts, ts_dist,
                                             "{}.png".format(out_path),
                                             ylabel=metric,
                                             dist_ylabel="",
                                             dist_plot_type="scatter",
                                             dist_ylim=[0 - 0.5, n - 1 + 0.5],
                                             dist_yticks=hidden_state_ticks,
                                             dist_ytick_labels=(
                                                 hidden_state_tick_labels),
                                             compress=True)

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


class DiscreteHMM(HMM):
    def set_emission(self):
        m = len(self.B[0])  # num of symbols
        self.emission_domain = ghmm.IntegerRange(0, m)
        self.emission_distr = ghmm.DiscreteDistribution(self.emission_domain)

    def get_obs_seqs(self, seqs):
        # transform seqs in bin_seqs
        bin_seqs = []
        for seq in seqs:
            bin_seqs.append(self.get_bin_list(seq))
        return bin_seqs

    def get_bin(self, y):
        if y >= 0.0 and y <= 0.01:
            return 0
        elif y > 0.01 and y < 0.03:
            return 1
        elif y >= 0.3 and y <= 0.05:
            return 2
        return 3

    def get_bin_list(self, l):
        ret = []
        for x in l:
            ret.append(self.get_bin(x))
        return ret


class GaussianHMM(HMM):
    def set_emission(self):
        self.emission_domain = ghmm.Float()
        self.emission_distr = ghmm.GaussianDistribution(self.emission_domain)

    def get_obs_seqs(self, seqs):
        return copy.deepcopy(seqs)

targets = [["64:66:B3:4F:FE:CE", "SNEDTCPROB01", "05-11-2016", "05-20-2016"],
           ["64:66:B3:7B:9B:B8", "SOODTCLDM24", "05-11-2016", "05-20-2016"],
           ["64:66:B3:7B:A4:1C", "SPOTVTSRV16", "05-01-2016", "05-10-2016"],
           ["64:66:B3:50:00:1C", "CPDGDTCLDM14", "05-11-2016", "05-20-2016"],
           ["64:66:B3:50:00:3C", "CPDGDTCLDM14", "05-11-2016", "05-20-2016"],
           ["64:66:B3:50:00:30", "CPDGDTCLDM14", "05-11-2016", "05-20-2016"],
           ["64:66:B3:50:06:82", "NHODTCSRV04", "05-11-2016", "05-20-2016"],
           ["64:66:B3:A6:9E:DE", "SPOTVTSRV16", "05-01-2016", "05-10-2016"],
           ["64:66:B3:A6:A9:16", "SPOTVTSRV16", "05-01-2016", "05-10-2016"],
           ["64:66:B3:A6:AE:76", "SNEDTCPROB01", "05-11-2016", "05-20-2016"],
           ["64:66:B3:A6:B3:B0", "SOODTCLDM24", "05-11-2016", "05-20-2016"],
           ["64:66:B3:A6:BC:D8", "SJCDTCSRV01", "05-11-2016", "05-20-2016"],
           ["64:66:B3:A6:A0:78", "AMRDTCPEV01", "05-01-2016", "05-10-2016"]]


def create_dirs():
    for dir in ["./plots/"]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def get_datetime(strdate):
    day = int(strdate.split("-")[1])
    month = int(strdate.split("-")[0])
    year = int(strdate.split("-")[2])
    return datetime.datetime(year, month, day)


def get_tp_params(tp):
    mac, server, date_start, date_end = tp[0], tp[1], tp[2], tp[3]
    dt_start = get_datetime(date_start)
    dt_end = get_datetime(date_end)
    return mac, server, dt_start, dt_end


def get_ts(tp):
    mac, server, dt_start, dt_end = get_tp_params(tp)
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
    in_path = "../input/{}/{}/{}.csv".format(date_dir, server, mac)
    ts = TimeSeries(in_path, metric, dt_start, dt_end)
    return ts


def process_train_with_all(hmm, A, B, pi, model_name):
    """train hmm with all sequences and apply viterbi in all"""

    seqs = []
    for tp in targets:
        ts = get_ts(tp)
        seqs.append(ts.raw_y)

    hmm.train(A, B, pi, seqs, "./plots/{}".format(model_name))

    for tp in targets:
        mac, server, dt_start, dt_end = get_tp_params(tp)
        out_path = ("./plots/{}_server{}_mac{}_dtstart{}_dtend{}".
                    format(model_name, server, mac, dt_start, dt_end))

        ts = get_ts(tp)
        hmm.viterbi(ts, out_path)


def process_train_individual(hmm, A, B, pi, model_name):
    """for each ts train a hmm and use the same hmm to check the best hidden
    state path"""

    for tp in targets:
        mac, server, dt_start, dt_end = get_tp_params(tp)
        ts = get_ts(tp)

        hmm.train(A, B, pi, [ts.raw_y], "./plots/{}".format(model_name))

        out_path = ("./plots/{}_server{}_mac{}_dtstart{}_dtend{}".
                    format(model_name, server, mac, dt_start, dt_end))
        hmm.viterbi(ts, out_path)


def process():
    create_dirs()

    # gaussian
    print "train_with_all gaussian_full"
    hmm = GaussianHMM()
    process_train_with_all(hmm, A_full_gauss, B_full_gauss, pi_full_gauss,
                           "train_with_all_gaussian_full")

    print "train_with_all gaussian_left_right"
    hmm = GaussianHMM()
    process_train_with_all(hmm, A_left_right_gauss, B_left_right_gauss,
                           pi_left_right_gauss,
                           "train_with_all_gaussian_left_right")

    print "train_individual gaussian_full"
    hmm = GaussianHMM()
    process_train_individual(hmm, A_full_gauss, B_full_gauss, pi_full_gauss,
                             "train_individual_gaussian_full")

    print "train_individual gaussian_left_right"
    hmm = GaussianHMM()
    process_train_individual(hmm, A_left_right_gauss, B_left_right_gauss,
                             pi_left_right_gauss,
                             "train_individual_gaussian_left_right")

    # discrete
    print "train_with_all discr_full"
    hmm = DiscreteHMM()
    process_train_with_all(hmm, A_full_discr, B_full_discr, pi_full_discr,
                           "train_with_all_discr_full")

    """
    print "train_with_all discr_left_right"
    hmm = DiscreteHMM()
    process_train_with_all(hmm, A_left_right_discr, B_left_right_discr,
                           pi_left_right_discr,
                           "train_with_left_right_discr")
    """

    print "train_individual discr_full"
    hmm = DiscreteHMM()
    process_train_individual(hmm, A_full_discr, B_full_discr, pi_full_discr,
                             "train_individual_discr_full")

    """
    print "train_individual discr_left_right"
    hmm = DiscreteHMM()
    process_train_individual(hmm, A_left_right_discr, B_left_right_discr,
                             pi_left_right_discr,
                             "train_individual_discr_left_right")
    """

process()
