import os
import math
import sys
import datetime
import numpy as np

sys.path.append("../../import_scripts/")
import plot_procedures
from time_series import TimeSeries

# PARAMETERS
dt_start = datetime.datetime(2015, 12, 1)
dt_end = datetime.datetime(2015, 12, 7)
metric = "loss"

max_segs = 10  # not used in O(n**2) solution
min_seg_len = 1
# cost_type = "mse"
# cost_type = "lik_normal"
cost_type = "lik_exp"
# cost_type = "lik_poisson"
# penalization_type = "aic"
penalization_type = "sic"
# penalization_type = "hannan_quinn"


def penalization(n, k):
    if penalization_type == "aic":
        return 0.1 * k
    elif penalization_type == "sic":
        return 2 * np.log(n) * k
    elif penalization_type == "hannan_quinn":
        return 2 * np.log(np.log(n)) * k


def penalization_linear(n):
    if penalization_type == "aic":
        return 2
    elif penalization_type == "sic":
        return 2 * np.log(n)
    elif penalization_type == "hannan_quinn":
        return 2 * np.log(np.log(n))


def get_mean(i, j):
    return np.float(prefix_sum[j] - prefix_sum[i - 1]) / (j - i + 1)


def seg_is_degenerate(i, j):
    if same_left[j] >= (j - i + 1):
        return True
    return False


def calc_same_left(data):
    global same_left
    n = len(data)
    same_left = np.zeros(n + 1)
    same_left[1] = 1
    for i in xrange(2, n + 1):
        if data[i - 1 - 1] == data[i - 1]:
            same_left[i] = 1 + same_left[i - 1]
        else:
            same_left[i] = 1


def calc_prefix_sum(data):
    global prefix_sum
    n = len(data)
    prefix_sum = np.zeros(n + 1)
    prefix_sum[0] = 0
    for i in xrange(1, n + 1):
        prefix_sum[i] = prefix_sum[i - 1] + data[i - 1]


def calc_mse(data):
    global mse
    n = len(data)
    mse = np.zeros(shape=(n + 1, n + 1))
    for i in xrange(1, n + 1):
        mse[i][i] = 0
        for j in xrange(i + 1, n + 1):
            mse[i][j] = mse[i][j - 1]
            mse[i][j] += (np.float(j - i) / (j - i + 1) *
                          (data[j - 1] - get_mean(i, j - 1)) ** 2)


def calc_normal_log_lik(data):
    global normal_log_lik
    n = len(data)
    normal_log_lik = np.zeros(shape=(n + 1, n + 1))
    for i in xrange(1, n + 1):
        for j in xrange(i + 1, n + 1):
            if (seg_is_degenerate(i, j)):
                continue
            squared_std = mse[i][j]
            normal_log_lik[i][j] = (-0.5 * (j - i + 1) *
                                    np.log(2 * np.pi * squared_std) -
                                    0.5 * (j - i + 1))


def calc_exp_log_lik(data):
    global exp_log_lik
    n = len(data)
    exp_log_lik = np.zeros(shape=(n + 1, n + 1))
    for i in xrange(1, n + 1):
        for j in xrange(i + 1, n + 1):
            if (seg_is_degenerate(i, j)):
                continue
            lmbd = np.float(j - i + 1) / (prefix_sum[j] - prefix_sum[i - 1])
            exp_log_lik[i][j] = ((j - i + 1) * np.log(lmbd) - lmbd *
                                 (prefix_sum[j] - prefix_sum[i - 1]))


def calc_prefix_sum_log_fact(data):
    global prefix_sum_log_fact
    n = len(data)
    prefix_sum_log_fact = np.zeros(shape=n + 1)
    for i in xrange(1, n + 1):
        prefix_sum_log_fact[i] = \
            (math.log(math.factorial(int(data[i - 1] * 100))) +
             prefix_sum_log_fact[i - 1])


def calc_poisson_log_lik(data):
    global poisson_log_lik
    n = len(data)
    poisson_log_lik = np.zeros(shape=(n + 1, n + 1))
    for i in xrange(1, n + 1):
        for j in xrange(i + 1, n + 1):
            if (seg_is_degenerate(i, j)):
                continue
            lmbd = float(prefix_sum[j] - prefix_sum[i - 1]) / (j - i + 1)
            poisson_log_lik[i][j] = (-(j - i + 1) * lmbd +
                                     (prefix_sum[j] - prefix_sum[i - 1]) *
                                     math.log(lmbd) -
                                     (prefix_sum_log_fact[j] -
                                      prefix_sum_log_fact[i - 1]))


def seg_cost(i, j):
    # seg has only one value: degenerate distribution
    if ("lik" in cost_type) and seg_is_degenerate(i, j):
        return (-2 * np.log(1), "lik_degenerate")

    if cost_type == "mse":
        return (2 * mse[i][j], "mse")
    elif cost_type == "lik_normal":
        return (-2 * normal_log_lik[i][j], "lik_normal")
    elif cost_type == "lik_exp":
        return (-2 * exp_log_lik[i][j], "lik_exp")
    elif cost_type == "lik_poisson":
        return (-2 * poisson_log_lik[i][j], "lik_poisson")


def write_cps(cps, seg_types, ts, out_path):
    with open("{}_change_points.csv".format(out_path), "w") as f:
        f.write("change_point\n")
        for cp in cps:
            f.write(str(ts.raw_x[cp - 1]) + "\n")

    with open("{}_seg_types.csv".format(out_path), "w") as f:
        f.write("seg_type,left_point,right_point\n")
        for p in seg_types:
            f.write("{},{},{}".format(p[0], ts.raw_x[p[1] - 1],
                                      ts.raw_x[p[2] - 1]))


def seg_neighbourhood(in_path, out_path, dt_start, dt_end):
    ts = TimeSeries(in_path, metric, dt_start, dt_end)
    n = len(ts.y)

    calc_same_left(ts.y)
    calc_prefix_sum(ts.y)
    calc_mse(ts.y)
    if cost_type == "lik_exp":
        calc_exp_log_lik(ts.y)
    elif cost_type == "lik_normal":
        calc_normal_log_lik(ts.y)
    elif cost_type == "lik_poisson":
        calc_prefix_sum_log_fact(ts.y)
        calc_poisson_log_lik(ts.y)

    # calculate dp
    dp = np.zeros(shape=(max_segs + 1, n + 1))
    for i in xrange(1, n + 1):
        dp[0][i] = float("inf")
    for n_segs in xrange(1, max_segs + 1):
        print n_segs
        for i in xrange(1, n + 1):
            dp[n_segs][i] = float("inf")
            for j in xrange(1, i - min_seg_len + 1 + 1):
                if seg_is_degenerate(j, i):
                    continue
                dp[n_segs][i] = min(dp[n_segs][i],
                                    dp[n_segs - 1][j - 1] + seg_cost(j, i)[0])

    # get best number of segs
    best_n_segs = 1
    for n_segs in xrange(2, max_segs + 1):
        if dp[n_segs][n] + penalization(n, n_segs) <= \
                dp[best_n_segs][n] + penalization(n, best_n_segs):
            best_n_segs = n_segs

    # backtrack: get change points
    seg_types, cps = [], []
    i, n_segs = n, best_n_segs
    while n_segs > 1:
        for j in range(1, i - min_seg_len + 1 + 1):
            if seg_is_degenerate(j, i):
                continue
            if np.isclose(dp[n_segs][i],
                          dp[n_segs - 1][j - 1] + seg_cost(j, i)[0]):
                seg_types.append((seg_cost(j, i)[1], j, i))
                cps.append(j)  # CHECK THIS INDEX
                i = j - 1
                n_segs -= 1
                break
    if (len(cps) > 0) and (cps[-1] > 1):
        seg_types.append((seg_cost(1, cps[-1] - 1)[1], 1, cps[-1] - 1))

    write_cps(cps, seg_types, ts, out_path)

    dt_cps = []
    for cp in cps:
        dt_cps.append(ts.raw_x[cp - 1])
    plot_procedures.plot_ts(ts, out_path + ".png", ylabel="loss",
                            ylim=[-0.02, 1.02], dt_axvline=dt_cps,
                            compress=True)


def create_dirs():
    if not os.path.exists("./plots/"):
        os.makedirs("./plots/")


def get_datetime(strdate):
    day = int(strdate.split("-")[1])
    month = int(strdate.split("-")[0])
    year = int(strdate.split("-")[2])
    return datetime.datetime(year, month, day)


def process():
    targets = [["64:66:B3:4F:FE:CE", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:7B:9B:B8", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:7B:A4:1C", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:50:00:1C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:00:3C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:00:30", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:06:82", "NHODTCSRV04", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:9E:DE", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:A6:A9:16", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:A6:AE:76", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:B3:B0", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:BC:D8", "SJCDTCSRV01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:A0:78", "AMRDTCPEV01", "05-01-2016",
                "05-10-2016"]]

    for tp in targets:
        mac, server, date_start, date_end = tp[0], tp[1], tp[2], tp[3]
        dt_start = get_datetime(date_start)
        dt_end = get_datetime(date_end)
        date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
        in_path = "../input/{}/{}/{}.csv".format(date_dir, server, mac)
        out_path = ("./plots/server{}_mac{}_datestart{}_dateend{}".
                    format(server, mac, date_start, date_end))

        create_dirs()
        seg_neighbourhood(in_path, out_path, dt_start, dt_end)

process()
