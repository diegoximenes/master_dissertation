from math import sqrt
import numpy as np
# import pyemd


def get_bin(sample, bins):
    bin = 0
    while bin < len(bins):
        if sample <= bins[bin]:
            break
        bin += 1
    return bin


def get_distr(samples, bins):
    hist = [0] * len(bins)

    for x in samples:
        bin = get_bin(x, bins)
        if bin < len(hist):
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


def mean_dist(l1, l2):
    return abs(np.mean(l1) - np.mean(l2))


def relative_mean_dist(l1, l2):
    den = max(1.0, abs(np.mean(l1)), abs(np.mean(l2)))
    return abs(np.mean(l1) - np.mean(l2)) / den


def emd(l1, l2, bins):
    distr1 = get_distr(l1, bins)
    distr2 = get_distr(l2, bins)
    dist_mat = [[0.0] * len(distr1) for i in xrange(len(distr1))]
    for i in xrange(len(distr1)):
        for j in xrange(len(distr1)):
            dist_mat[i][j] = float(abs(j - i))
    return pyemd.emd(np.asarray(distr1), np.asarray(distr2),
                     np.asarray(dist_mat))
