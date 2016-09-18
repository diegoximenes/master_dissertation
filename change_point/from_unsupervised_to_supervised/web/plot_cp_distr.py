import pandas as pd
import matplotlib
import matplotlib.pylab as plt
import numpy as np


def cp_distr():
    df = pd.read_csv("./cnt_cps_per_ts_samples.csv")
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
    plt.savefig("./cps_per_ts.png")


def middle_length_distr():
    df = pd.read_csv("./middle_segment_length_samples.csv")
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
    plt.savefig("./middle_segment_length.png")


def first_length_distr():
    df = pd.read_csv("./first_segment_length_samples.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 26})
    plt.gcf().set_size_inches(15, 13)
    plt.hist(df["samples"], bins=range(0, 500, 20), normed=True)
    plt.xticks(rotation=45)
    plt.xlabel("First Segment Length")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./first_segment_length_samples.png")


def last_length_distr():
    df = pd.read_csv("./last_segment_length_samples.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 26})
    plt.gcf().set_size_inches(15, 13)
    plt.hist(df["samples"], bins=range(0, 500, 20), normed=True)
    plt.xticks(rotation=45)
    plt.xlabel("Last Segment Length")
    plt.ylabel("Frequency")
    plt.grid()
    plt.savefig("./last_segment_length_samples.png")


def abs_diff_mean_segs():
    df = pd.read_csv("./abs_diff_mean_consecutive_segments.csv")
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
    plt.savefig("./mean_abs_diff_consecutive_segs.png")


def hellinger():
    df = pd.read_csv("./hellinger_dist_consecutive_segments.csv")
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
    plt.savefig("./hellinger_consecutive_segs.png")


if __name__ == "__main__":
    # cp_distr()
    # middle_length_distr()
    # first_length_distr()
    # last_length_distr()
    abs_diff_mean_segs()
    hellinger()
