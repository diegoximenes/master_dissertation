from math import sqrt
import numpy as np


def get_distr(samples, bins):
    bins = np.arange(0.02, 10.0 + 0.02, 0.02)
    hist = [0] * len(bins)

    for x in samples:
        bin = 0
        while bin < len(bins):
            if x <= bins[bin]:
                break
            bin += 1
        hist[bin] += 1

    return np.asarray(hist) / float(np.sum(hist))


def hellinger_dist(l1, l2, bins):
    distr1 = get_distr(l1, bins)
    distr2 = get_distr(l2, bins)

    dist = 0.0
    for i in xrange(len(distr1)):
        dist += (sqrt(distr1[i]) - sqrt(distr2[i])) ** 2
    dist /= 2.0
    dist = sqrt(dist)
    return dist
