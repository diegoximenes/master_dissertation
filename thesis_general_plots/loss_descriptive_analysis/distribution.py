import pandas as pd
import matplotlib
import matplotlib.pylab as plt
import numpy as np


def write_distribution_cdf(samples):
    bin_cnt = {}
    cnt_all = 0
    for bin in np.arange(0.0, 1.01, 0.01):
        bin_cnt[str(bin)] = 0
    for sample in samples:
        if str(sample) not in bin_cnt:
            print "ERROR: {} not in bin_cnt".format(sample)
        else:
            bin_cnt[str(sample)] += 1
            cnt_all += 1

    with open("./plots/distribution/distribution.csv", "w") as f:
        f.write("bin,fraction\n")
        for bin in sorted(bin_cnt.keys()):
            f.write("{},{}\n".format(bin, float(bin_cnt[bin]) / cnt_all))

    sum = 0.0
    with open("./plots/distribution/cdf.csv", "w") as f:
        f.write("bin,fraction\n")
        for bin in sorted(bin_cnt.keys()):
            sum += float(bin_cnt[bin]) / cnt_all
            f.write("{},{}\n".format(bin, sum))


def plot_cdf():
    df = pd.read_csv("./plots/distribution/cdf.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 13})
    plt.gcf().set_size_inches(15, 12)
    plt.xticks(np.arange(0.0, 1.05, 0.05))
    plt.xlabel("X")
    plt.ylim(0.93, 1.001)
    plt.xlim(-0.005, 1.005)
    plt.ylabel("P[loss fraction $\leq$ X]")
    plt.grid()
    plt.plot(df["bin"], df["fraction"], linewidth=2.0, marker="o")
    plt.savefig("./plots/distribution/loss_cdf.png")


def plot_distr():
    df = pd.read_csv("./plots/distribution/distribution.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 13})
    plt.gcf().set_size_inches(15, 12)
    plt.grid()
    ax = plt.figure().gca()
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_xlabel("loss fraction")
    ax.set_ylabel("frequency")
    ax.scatter(df["bin"][1:len(df["bin"]) - 1],
               df["fraction"][1:len(df["bin"]) - 1] / df["fraction"][0], s=50,
               marker="x")
    plt.savefig("./plots/distribution/distr.png")


if __name__ == "__main__":
    # df = pd.read_csv("./plots/distribution/samples.csv")
    # write_distribution_cdf(df["loss"])

    # plot_cdf()
    plot_distr()
