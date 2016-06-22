import os
import math
import sys
import numpy as np
from pyemd import emd

sys.path.append("../../import_scripts/")
import plot_procedures
import time_series
from time_series import TimeSeries

# PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
window_len = 24
dist_type = "hellinger"
# dist_type = "mean"
# dist_type = "emd"
# dist_type = "bhattacharyya"
# dist_type = "jensen_shannon"

date_dir = str(target_year) + "_" + str(target_month).zfill(2)


def get_bins():
    if metric == "loss":
        delta, min_bin, max_bin = 0.01, 0.01, 1
    bins = np.arange(min_bin, max_bin + delta, delta)
    return bins

emd_dist_matrix = []


def set_emd_dist_matrix():
    global emd_dist_matrix
    bins = get_bins()
    for i in xrange(len(bins)):
        l = []
        for j in xrange(len(bins)):
            l.append(abs(i - j) * 1.0 / len(bins))
        emd_dist_matrix.append(l)
    emd_dist_matrix = np.array(emd_dist_matrix) * 1.0
if dist_type == "emd":
    set_emd_dist_matrix()


def create_dirs(server):
    if not os.path.exists("./plots/"):
        os.makedirs("./plots/")
    if not os.path.exists("./plots/sliding_window/"):
        os.makedirs("./plots/sliding_window/")
    if not os.path.exists("./plots/sliding_window/" + date_dir):
        os.makedirs("./plots/sliding_window/" + date_dir)
    if not os.path.exists("./plots/sliding_window/" + date_dir + "/" + server):
        os.makedirs("./plots/sliding_window/" + date_dir + "/" + server)


def bhattacharyya_coef(distr1, distr2):
    sum1, sum2, coef = np.sum(distr1), np.sum(distr2), 0
    # no distribution
    if (sum1 == 0) or (sum2 == 0):
        return None
    for i in range(len(distr1)):
        coef += math.sqrt(float(distr1[i]) / float(sum1) *
                          float(distr2[i]) / float(sum2))
    return coef


def bhattacharyya_dist(distr1, distr2):
    bhat_coef = bhattacharyya_coef(distr1, distr2)
    if (bhat_coef is None) or (bhat_coef == 0):
        return None
    return -math.log(bhat_coef)


def hellinger_dist(distr1, distr2):
    bhat_coef = bhattacharyya_coef(distr1, distr2)
    if bhat_coef is None:
        return None
    return math.sqrt(1 - bhat_coef)


def get_hist(l):
    bins = get_bins()
    hist = [0] * len(bins)

    for x in l:
        bin = 0
        while bin < len(bins):
            if x <= bins[bin]:
                break
            bin += 1
        hist[bin] += 1

    return np.asarray(hist)


def get_distr(l):
    hist = get_hist(l)
    return np.asarray(hist) / float(np.sum(hist))


def mean_dist(l1, l2):
    return abs(np.mean(l1) - np.mean(l2))


def kl_divergence(distr1, distr2):
    ret = 0
    for i in xrange(len(distr1)):
        if distr1[i] > 0:
            ret += distr1[i] * math.log(distr1[i] / distr2[i])
    return ret


def jensen_shannon_divergence(distr1, distr2):
    m = (distr1 + distr2) / 2.0
    return 0.5 * (kl_divergence(distr1, m) + kl_divergence(distr2, m))


def distance(l1, l2):
    distr1 = get_distr(l1)
    distr2 = get_distr(l2)

    if dist_type == "mean":
        return mean_dist(l1, l2)
    elif dist_type == "hellinger":
        return hellinger_dist(distr1, distr2)
    elif dist_type == "emd":
        return emd(distr1 * 1.0, distr2 * 1.0, emd_dist_matrix * 1.0)
    elif dist_type == "bhattacharyya":
        return bhattacharyya_dist(distr1, distr2)
    elif dist_type == "jensen_shannon":
        return jensen_shannon_divergence(distr1, distr2)


def sliding_window(in_file_path, out_file_path):
    ts = TimeSeries(in_file_path, target_month, target_year, metric)
    ts_compressed = time_series.get_compressed(ts)

    ts_dist = time_series.dist_ts(ts)
    for i in range(window_len, len(ts_compressed.y) - window_len + 1):
        dt = ts_compressed.x[i]
        dist = distance(ts_compressed.y[i - window_len:i],
                        ts_compressed.y[i:i + window_len])

        if dist is not None:
            ts_dist.dt_mean[dt] = dist
            ts_dist.x.append(dt)
            ts_dist.y.append(dist)

    dist_ylim = None
    if ((dist_type == "hellinger") or
            (metric == "loss" and dist_type == "mean")):
        dist_ylim = [-0.01, 1.01]
    plot_procedures.plot_ts_share_x(ts, ts_dist,
                                    out_file_path + "_" + dist_type + ".png",
                                    ylabel=metric,
                                    dist_ylabel=dist_type + " dist",
                                    dist_ylim=dist_ylim)


def get_change_points():
    cnt = 0

    mac = "64:66:B3:50:03:A2"
    server = "NHODTCSRV04"
    sliding_window("../input/" + date_dir + "/" + server + "/" + mac + ".csv",
                   "./test")
    return

    for server in os.listdir("../input/" + date_dir + "/"):
        print server
        create_dirs(server)
        for file_name in os.listdir("../input/%s/%s" % (date_dir, server)):
            mac = file_name.split(".")[0]
            cnt += 1
            print "cnt=" + str(cnt)

            in_file_path = "../input/%s/%s/%s.csv" % (date_dir, server, mac)
            out_file_path = "./plots/sliding_window/%s/%s/%s" % (date_dir,
                                                                 server, mac)

            sliding_window(in_file_path, out_file_path)

get_change_points()
