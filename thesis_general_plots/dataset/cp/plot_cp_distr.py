import pandas as pd
import matplotlib
import matplotlib.pylab as plt
import numpy as np


def cp_distr():
    df = pd.read_csv("./plots/distr/cps_per_ts_samples.csv")
    weights = np.asarray([1.0 / len(df["samples"])] * len(df["samples"]))
    print "cnt_cps={}".format(df["samples"].sum())
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.hist(df["samples"], bins=range(df["samples"].max() + 1),
             weights=weights)
    plt.xticks(range(df["samples"].max() + 2), rotation=45)
    plt.xlabel("Number of Changes Points per Time Series")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./plots/distr/cps_per_ts.png")


def middle_length_distr():
    df = pd.read_csv("./plots/distr/middle_seg_len_samples.csv")
    weights = np.asarray([1.0 / len(df["samples"])] * len(df["samples"]))
    print "min={}, max={}".format(df["samples"].min(), df["samples"].max())
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.hist(df["samples"], bins=range(0, 360, 10),
             weights=weights)
    plt.xticks(rotation=45)
    plt.xlabel("Segment Length")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./plots/distr/middle_segment_length.png")


def abs_mean_diff_segs():
    df = pd.read_csv("./plots/distr/abs_mean_diff_consecutive_segs.csv")
    weights = np.asarray([1.0 / len(df["samples"])] * len(df["samples"]))
    print "min={}, max={}".format(df["samples"].min(), df["samples"].max())
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.hist(df["samples"], bins=np.arange(0.0, 0.6, 0.02),
             weights=weights)
    plt.xticks(rotation=45)
    plt.xlabel("Mean Absolute Difference of Consecutive Segments")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./plots/distr/abs_diff_consecutive_segs.png")


def hellinger():
    df = pd.read_csv("./plots/distr/hellinger_dist_consecutive_segs.csv")
    weights = np.asarray([1.0 / len(df["samples"])] * len(df["samples"]))
    print "min={}, max={}".format(df["samples"].min(), df["samples"].max())
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.hist(df["samples"], bins=np.arange(0.0, 1.02, 0.02),
             weights=weights)
    plt.xticks(rotation=45)
    plt.xlabel("Hellinger Distance of Consecutive Segments")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./plots/distr/hellinger_consecutive_segs.png")


if __name__ == "__main__":
    cp_distr()
    middle_length_distr()
    abs_mean_diff_segs()
    hellinger()
