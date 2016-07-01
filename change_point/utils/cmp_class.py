import os
import sys
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


def conf_mat(correct_class, pred_class, win_len):
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

    # is not clear if tn will be necessary
    conf = {}
    conf["tp"] = len(max_match) / 2
    conf["fp"] = len(pred_class) - conf["tp"]
    conf["fn"] = len(correct_class) - conf["tp"]

    return conf


def f1_score(conf):
    num = float(2 * conf["tp"])
    den = float(2 * conf["tp"] + conf["fp"] + conf["fn"])
    return num / den
