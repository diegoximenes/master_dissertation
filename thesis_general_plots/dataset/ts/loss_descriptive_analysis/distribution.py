import pandas as pd
import matplotlib
import matplotlib.pylab as plt
import numpy as np
from scipy import stats


def write_distr_cdf_ccdf(samples):
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

    sum = 0.0
    with open("./plots/distribution/ccdf.csv", "w") as f:
        f.write("bin,fraction\n")
        for bin in sorted(bin_cnt.keys()):
            sum += float(bin_cnt[bin]) / cnt_all
            f.write("{},{}\n".format(bin, 1 - sum))


def plot_cdf():
    df = pd.read_csv("./plots/distribution/cdf.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.xticks(np.arange(0.0, 1.05, 0.05), rotation=45)
    plt.xlabel("X")
    plt.ylim(0.93, 1.001)
    plt.xlim(-0.005, 1.005)
    plt.ylabel("P[Loss Fraction $\leq$ X]")
    plt.grid()
    plt.plot(df["bin"], df["fraction"], linewidth=2.0, marker="o")
    plt.savefig("./plots/distribution/cdf.png")


def plot_ccdf():
    df = pd.read_csv("./plots/distribution/ccdf.csv")
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.grid()
    ax = plt.figure(figsize=(16, 15)).gca()
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_xlabel("X")
    ax.set_ylabel("P[Loss Fraction > X]")
    ax.scatter(df["bin"][1:-2], df["fraction"][1:-2], marker="x", s=50)
    plt.savefig("./plots/distribution/ccdf.png")


def plot_distr():
    df = pd.read_csv("./plots/distribution/distribution.csv")

    x = np.arange(0.01, 1.0, 0.02)
    y = [0] * 50

    for idx, row in df.iterrows():
        if int(100 * row["bin"] != 100):
            print "row[bin]={}".format(row["bin"])
            print "100 * row[bin]={}".format(int(100 * row["bin"]) / 2)
            y[int(100 * row["bin"]) / 2] += float(row["fraction"])

    plt.clf()
    matplotlib.rcParams.update({'font.size': 13})
    plt.gcf().set_size_inches(15, 13)
    plt.grid()
    ax = plt.figure().gca()
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_xlabel("loss fraction")
    ax.set_ylabel("frequency")
    ax.scatter(x, y, marker="x")
    plt.show()
    # ax.scatter(df["bin"][1:len(df["bin"]) - 1],
    #            df["fraction"][1:len(df["bin"]) - 1] / df["fraction"][0],
    #            s=50, marker="x")
    # plt.savefig("./plots/distribution/distr.png")


def fit_geom():
    df = pd.read_csv("./plots/distribution/samples.csv")
    samples = map(lambda x: int(100 * x), df["samples"])
    n = len(samples)
    p = float(n) / (sum(samples) + n)
    print "p={}".format(p)

    x_geom = range(101)
    y_geom = map(lambda x: p * (1.0 - p)**x, x_geom)
    print y_geom
    plt.clf()
    # plt.hist(samples, bins=range(101), normed=True, log=True)
    plt.plot(x_geom, y_geom)
    plt.show()


def fit_exp():
    df = pd.read_csv("./plots/distribution/samples.csv")
    samples = df["samples"]
    lamb = float(len(samples)) / sum(samples)

    stats.probplot(samples, dist="expon", plot=plt)
    plt.show()

    x_exp = np.arange(0.0, 1.01, 0.01)
    y_exp = map(lambda x: lamb * np.e ** (-lamb * x), x_exp)
    plt.clf()
    plt.plot(x_exp, y_exp)
    plt.show()


if __name__ == "__main__":
    df = pd.read_csv("./plots/distribution/samples.csv")
    write_distr_cdf_ccdf(df["samples"])
    plot_ccdf()
    plot_cdf()
    # plot_distr()
    # fit_geom()
    # fit_exp()
