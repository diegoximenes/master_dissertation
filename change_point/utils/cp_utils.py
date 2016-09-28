import os
import sys
import functools
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def param_pp(dic):
    """
    pretty print: swap function elements by their name
    """
    ret_dic = {}
    for key in dic:
        if callable(dic[key]):
            if isinstance(dic[key], functools.partial):
                ret_dic[key] = dic[key].func.func_name
            else:
                ret_dic[key] = dic[key].__name__
        else:
            ret_dic[key] = dic[key]
    return ret_dic


def from_str_to_int_list(str_l):
    if pd.isnull(str_l):
        ret = []
    else:
        ret = sorted(map(int, str_l.split(",")))
    return ret


def unpack_pandas_row(row):
    dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
    dt_end = dt_procedures.from_js_strdate_to_dt(row["date_end"])
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
    in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir, row["server"],
                                             row["mac"])
    return in_path, dt_start, dt_end


def preprocess(ts, preprocess_args):
    if preprocess_args["filter_type"] == "ma_smoothing":
        ts.ma_smoothing(preprocess_args["win_len"])
    elif preprocess_args["filter_type"] == "median_filter":
        ts.median_filter(preprocess_args["win_len"])
    elif preprocess_args["filter_type"] == "savgol":
        ts.savgol(preprocess_args["win_len"], preprocess_args["poly_order"])
    elif preprocess_args["filter_type"] == "percentile_filter":
        ts.percentile_filter(preprocess_args["win_len"],
                             preprocess_args["p"])


def get_ts(row, preprocess_args):
    in_path, dt_start, dt_end = unpack_pandas_row(row)
    ts = TimeSeries(in_path, "loss", dt_start, dt_end)
    preprocess(ts, preprocess_args)
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


def get_f_dist(f_dist, bin_size_f_dist):
    if f_dist.__name__ == "mean_dist":
        return f_dist

    bins = np.arange(0.0, 1.0 + bin_size_f_dist, bin_size_f_dist)
    p_f_dist = functools.partial(f_dist, bins=bins)
    return p_f_dist
