import os
import sys
import numpy as np
import pandas as pd
from hopcroftkarp import HopcroftKarp

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def unpack_pandas_row(row):
    dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
    dt_end = dt_procedures.from_js_strdate_to_dt(row["date_end"])
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
    in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir, row["server"],
                                             row["mac"])
    return in_path, dt_start, dt_end


def get_ts(row, preprocess_args):
    in_path, dt_start, dt_end = unpack_pandas_row(row)
    ts = TimeSeries(in_path, "loss", dt_start, dt_end)

    if preprocess_args["filter_type"] == "ma_smoothing":
        ts.ma_smoothing(preprocess_args["win_len"])
    elif preprocess_args["filter_type"] == "median_filter":
        ts.median_filter(preprocess_args["win_len"])
    elif preprocess_args["filter_type"] == "savgol":
        ts.savgol(preprocess_args["win_len"], preprocess_args["poly_order"])

    return ts


def valid_preprocess_args(preprocess_args):
    if ((preprocess_args["filter_type"] == "median_filter") and
            (preprocess_args["win_len"] % 2 == 0)):
        return False
    if preprocess_args["filter_type"] == "savgol":
        if preprocess_args["poly_order"] >= preprocess_args["win_len"]:
            return False
        if preprocess_args["win_len"] % 2 == 0:
            return False
    return True


def valid_param(param):
    return True


def from_str_to_int_list(str_l):
    if pd.isnull(str_l):
        ret = []
    else:
        ret = sorted(map(int, str_l.split(",")))
    return ret


def conf_mat(correct_class, pred_class, ts, win_len):
    """
    - description: return confusion matrix as dictionary. Match pred_class to
    correct_class maximizing number of true positives. One change point can be
    matched only once. By now solved with maximum matching in bipartite graph:
    nodes of the left represents change points of correct_class and the nodes
    of the right represents change points of pred_class. Two nodes are
    connected if the distance between than is less or equal than win_len. In
    case of more than one solution with maximum matching is possible to select
    the solution with minimum distance between matched change points, but for
    that, the problem must be solved with dynamic programming or
    min-cost-max-flow.
    - arguments:
        - correct_class: list with ids indicating change points of correct
        classification
        - pred_class : list with ids indicating change points of predicted
        classification
        - win_len: correct_class[i] can be matched with pred_class[j] if
        abs(correct_class[i] - pred_class[j]) <= win_len
    """

    graph = {}
    for l in xrange(len(correct_class)):
        neigh = set()
        for r in xrange(len(pred_class)):
            if abs(correct_class[l] - pred_class[r]) <= win_len:
                neigh.add("r{}".format(r))
        graph["l{}".format(l)] = neigh
    max_match = HopcroftKarp(graph).maximum_matching()

    conf = {}
    conf["tp"] = len(max_match) / 2
    conf["fp"] = len(pred_class) - conf["tp"]
    conf["fn"] = len(correct_class) - conf["tp"]
    # tn = number of true not change points - number of wrong predicted change
    # points
    # tn = (number of points - number of true change points) - number of wrong
    # predicted change points
    conf["tn"] = len(ts.y) - len(correct_class) - conf["fp"]

    return conf


def f_beta_score(beta, conf):
    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    num = float((1 + beta ** 2) * tp)
    den = float((1 + beta ** 2) * tp + beta ** 2 * fn + fp)

    if np.isclose(den, 0.0):
        return None
    return num / den


def f_half_score(conf):
    return f_beta_score(0.5, conf)


def f_1_score(conf):
    return f_beta_score(1.0, conf)


def f_2_score(conf):
    return f_beta_score(2.0, conf)


def jcc(conf):
    """
    jaccard's coefficient of community
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    num = float(tp)
    den = float(tp + fp + fn)

    if np.isclose(den, 0.0):
        return None
    return num / den


def acc(conf):
    """
    accuracy
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    tn = conf["tn"]
    p = tp + fn
    n = fp + tn
    num = float(tp + tn)
    den = float(p + n)

    if np.isclose(den, 0.0):
        return None
    return num / den


def bacc(conf):
    """
    balanced accuracy
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    tn = conf["tn"]
    p = tp + fn
    n = fp + tn

    if np.isclose(p, 0.0) or np.isclose(n, 0.0):
        return None
    return (float(tp) / p + float(tn) / n) / 2.0


def csi(conf):
    """
    classification success index
    """

    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]

    if np.isclose(tp + fp, 0.0) or np.isclose(tp + fn, 0.0):
        return None

    ppv = float(tp) / float(tp + fp)
    tpr = float(tp) / float(tp + fn)
    return ppv + tpr - 1
