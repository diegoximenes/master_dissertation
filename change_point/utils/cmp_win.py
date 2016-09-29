from math import sqrt
import numpy as np
import pyemd


def get_distr(samples, bins):
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


def mean_dist(l1, l2):
    return abs(np.mean(l1) - np.mean(l2))


def emd(l1, l2, bins):
    distr1 = get_distr(l1, bins)
    distr2 = get_distr(l2, bins)
    dist_mat = [[0.0] * len(distr1) for i in xrange(len(distr1))]
    for i in xrange(len(distr1)):
        for j in xrange(len(distr1)):
            dist_mat[i][j] = float(abs(j - i))
    return pyemd.emd(np.asarray(distr1), np.asarray(distr2),
                     np.asarray(dist_mat))


def hmm_win_dist(l1, l2, n, bins=[]):
    distr1 = [0] * n
    distr2 = [0] * n
    for x in l1:
        distr1[x] += 1
    for x in l2:
        distr2[x] += 1
    dist = 0.0
    for i in xrange(n):
        distr1[i] /= float(n)
        distr2[i] /= float(n)
        dist += abs(distr1[i] - distr2[i])
    dist /= 2.0
    return dist
