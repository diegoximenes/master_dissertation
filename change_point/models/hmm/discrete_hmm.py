import os
import sys
import ghmm
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pylab as plt

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
# import utils.plot_procedures as plot_procedures
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cmp_win as cmp_win
import change_point.utils.cp_utils as cp_utils
import change_point.models.hmm.hmm as hmm
from utils.time_series import TimeSeries

script_dir = os.path.join(os.path.dirname(__file__), ".")


class DiscreteHMM(hmm.HMM):
    def __init__(self, preprocess_args, A, B, pi, obs_bins, win_len, thresh,
                 min_peak_dist):
        self.preprocess_args = preprocess_args
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

    # TODO
    def states_are_diff(self, state1, state2):
        return True


def create_dirs():
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/discrete/".format(script_dir)]:
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
    param = {"A": A,
             "B": B,
             "pi": pi,
             "obs_bins": obs_bins,
             "win_len": 6,
             "thresh": 0.8,
             "min_peak_dist": 6}

    hmm = DiscreteHMM(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        ts = cp_utils.get_ts(row, preprocess_args)
        pred, ts_hidden_state_path, ts_sliding_windows_dist = \
            hmm.viterbi_sliding_windows_pipeline(ts)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        # ts_hidden_state_change_lik = hmm.hidden_state_change_lik(ts)
        # hmm.print_model_to_file("./model.out")

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
        out_path = ("{}/plots/discrete/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts_raw = TimeSeries(in_path, "loss", dt_start, dt_end)

        # hidden state path
        plt.clf()
        matplotlib.rcParams.update({'font.size': 21})
        f, ax = plt.subplots(3, 1, figsize=(16, 12), sharex="col")
        ax[0].grid()
        ax[0].set_title("correct")
        ax[0].set_ylim([-0.02, 1.02])
        ax[0].set_yticks(np.arange(0.0, 1.0 + 0.05, 0.05))
        ax[0].set_xticks(range(0, len(ts_raw.y), 100))
        for xvline in correct:
            ax[0].axvline(xvline, color="r", linewidth=2.0)
        ax[0].scatter(range(len(ts_raw.y)), ts_raw.y)
        ax[1].grid()
        ax[1].set_title("hidden state path")
        ax[1].set_ylim([-1, len(param["A"])])
        ax[1].scatter(range(len(ts_hidden_state_path.y)),
                      ts_hidden_state_path.y)
        ax[2].grid()
        ax[2].set_title("sliding windows offline. conf={}".format(conf))
        ax[2].set_ylim([-0.02, 1.02])
        for xvline in pred:
            ax[2].axvline(xvline, color="r", linewidth=2.0)
        ax[2].plot(np.arange(len(ts_sliding_windows_dist.y)) +
                   param["win_len"], ts_sliding_windows_dist.y)
        plt.savefig(out_path)

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
