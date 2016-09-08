import sys
import numpy as np
from math import sqrt

sys.path.append("../../utils/")
import plot_procedures
from time_series import TimeSeries


def hellinger_dist(distr1, distr2):
    dist = 0.0
    for i in xrange(len(distr1)):
        dist += (sqrt(distr1[i]) - sqrt(distr2[i])) ** 2
    dist /= 2.0
    dist = sqrt(dist)
    return dist


def get_distr(l):
    bins = np.arange(0.02, 10.0 + 0.02, 0.02)
    hist = [0] * len(bins)

    for x in l:
        bin = 0
        while bin < len(bins):
            if x <= bins[bin]:
                break
            bin += 1
        hist[bin] += 1

    return np.asarray(hist) / float(np.sum(hist))


def distance(l1, l2):
    distr1 = get_distr(l1)
    distr2 = get_distr(l2)
    return hellinger_dist(distr1, distr2)


def simulate():
    ts_len = 1000
    l1 = np.random.normal(1, 0.2, ts_len)
    l2 = np.random.normal(5, 0.2, ts_len)
    l = np.append(l1, l2)

    ts = TimeSeries(compressed=True)
    ts.x = range(1, len(l) + 1)
    ts.y = l

    return ts


def sliding_window(ts):
    ts_dist = TimeSeries(compressed=True)

    win_len = 100
    for i in xrange(win_len, len(ts.y) - win_len + 1):
        dist = distance(ts.y[i - win_len:i], ts.y[i:i + win_len])
        ts_dist.x.append(ts.x[i])
        ts_dist.y.append(dist)

    plot_procedures.plot_ts_share_x(ts,
                                    ts_dist,
                                    "./sliding_window_toy_example.png",
                                    compress=True,
                                    plot_type1="plot",
                                    ylim1=[0, max(ts.y)],
                                    ylabel1="$y_{t}$",
                                    ylabel2="Hellinger Distance",
                                    xlabel="$t$")

if __name__ == "__main__":
    ts = simulate()
    sliding_window(ts)
