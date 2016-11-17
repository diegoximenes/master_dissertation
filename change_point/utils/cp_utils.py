import os
import sys
import ast
import functools
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def get_mac_traceroute_filtered(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = ("{}/change_point/unsupervised/prints/{}/filtered/"
               "traceroute_per_mac.csv".format(base_dir, str_dt))
    df = pd.read_csv(in_path)
    mac_traceroute = {}
    for idx, row in df.iterrows():
        if row["is_unique_traceroute"]:
            mac_traceroute[row["mac"]] = \
                ast.literal_eval(row["traceroute_filtered"])
    return mac_traceroute


def iter_names_traceroute_filtered(traceroute, only_cmts=False):
    def is_cmts(name):
        ip1 = name[0][1]
        ip2 = name[1][1]
        if utils.is_private_ip(ip1) and (not utils.is_private_ip(ip2)):
            return True
        return False

    for name in traceroute:
        if name[0][0] is None:
            continue
        splitted = name[0][0].split(".")
        if splitted[0] == "192" and splitted[1] == "168":
            continue

        if only_cmts and (not is_cmts(name)):
            continue

        yield name


def run_sequential(datasets, f, cmp_class_args, preprocess_args, param,
                   metric):
    for dataset in datasets:
        f(dataset, cmp_class_args, preprocess_args, param, metric)


def run_parallel(datasets, f, cmp_class_args, preprocess_args, param, metric):
    f_run = functools.partial(f, cmp_class_args=cmp_class_args,
                              preprocess_args=preprocess_args,
                              param=param, metric=metric)
    datasets = map(lambda x: [x], datasets)
    utils.parallel_exec(f_run, datasets)


def iter_unsupervised_datasets():
    for dt_dir in os.listdir("{}/change_point/input/unsupervised/".
                             format(base_dir)):
        yield "unsupervised/{}".format(dt_dir)


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
    dt_start = dt_procedures.from_strdt_to_dt(row["dt_start"])
    dt_end = dt_procedures.from_strdt_to_dt(row["dt_end"])
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    in_path = "{}/input/{}/{}/{}.csv".format(base_dir, dt_dir, row["server"],
                                             row["mac"])
    return in_path, dt_start, dt_end


def preprocess(ts, preprocess_args):
    if preprocess_args["filter_type"] == "ma_smoothing":
        ts.ma_smoothing(preprocess_args["win_len"])
    elif preprocess_args["filter_type"] == "savgol":
        ts.savgol(preprocess_args["win_len"], preprocess_args["poly_order"])
    elif preprocess_args["filter_type"] == "percentile_filter":
        ts.percentile_filter(preprocess_args["win_len"],
                             preprocess_args["p"])


def get_ts(row, preprocess_args, metric):
    in_path, dt_start, dt_end = unpack_pandas_row(row)
    ts = TimeSeries(in_path, metric, dt_start, dt_end)
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


def get_f_dist(f_dist, bin_size_f_dist, min_bin_f_dist, max_bin_f_dist):
    if isinstance(f_dist, functools.partial):
        f_dist_name = f_dist.func.func_name
    else:
        f_dist_name = f_dist.__name__

    if f_dist_name == "hellinger_dist":
        bins = np.arange(min_bin_f_dist, max_bin_f_dist + bin_size_f_dist,
                         bin_size_f_dist)
        p_f_dist = functools.partial(f_dist, bins=bins)
        return p_f_dist
    return f_dist


def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising',
                 kpsh=False, valley=False, show=False, ax=None):

    """
    ADAPTED FROM:
    https://github.com/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb
    ADAPTATIONS:
    - removed show and ax parameters
    - changed code to follow pep8

    Detect peaks in data based on their amplitude and other features.

    Parameters
    ----------
    x : 1D array_like
        data.
    mph : {None, number}, optional (default = None)
        detect peaks that are greater than minimum peak height.
    mpd : positive integer, optional (default = 1)
        detect peaks that are at least separated by minimum peak distance (in
        number of data).
    threshold : positive number, optional (default = 0)
        detect peaks (valleys) that are greater (smaller) than `threshold`
        in relation to their immediate neighbors.
    edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
        for a flat peak, keep only the rising edge ('rising'), only the
        falling edge ('falling'), both edges ('both'), or don't detect a
        flat peak (None).
    kpsh : bool, optional (default = False)
        keep peaks with same height even if they are closer than `mpd`.
    valley : bool, optional (default = False)
        if True (1), detect valleys (local minima) instead of peaks.
    show : bool, optional (default = False)
        if True (1), plot data in matplotlib figure.
    ax : a matplotlib.axes.Axes instance, optional (default = None).

    Returns
    -------
    ind : 1D array_like
        indeces of the peaks in `x`.

    Notes
    -----
    The detection of valleys instead of peaks is performed internally by simply
    negating the data: `ind_valleys = detect_peaks(-x)`

    The function can handle NaN's

    See this IPython Notebook [1]_.

    References
    ----------

    Examples
    --------
    >>> from detect_peaks import detect_peaks
    >>> x = np.random.randn(100)
    >>> x[60:81] = np.nan
    >>> # detect all peaks and plot data
    >>> ind = detect_peaks(x, show=True)
    >>> print(ind)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # set minimum peak height = 0 and minimum peak distance = 20
    >>> detect_peaks(x, mph=0, mpd=20, show=True)

    >>> x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
    >>> # set minimum peak distance = 2
    >>> detect_peaks(x, mpd=2, show=True)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # detection of valleys instead of peaks
    >>> detect_peaks(x, mph=0, mpd=20, valley=True, show=True)

    >>> x = [0, 1, 1, 0, 1, 1, 0]
    >>> # detect both edges
    >>> detect_peaks(x, edge='both', show=True)

    >>> x = [-2, 1, -2, 2, 1, 1, 3, 0]
    >>> # set threshold = 2
    >>> detect_peaks(x, threshold = 2, show=True)
    """

    x = np.atleast_1d(x).astype('float64')
    if x.size < 3:
        return np.array([], dtype=int)
    if valley:
        x = -x
    # find indices of all peaks
    dx = x[1:] - x[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(x))[0]
    if indnan.size:
        x[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) &
                           (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) &
                           (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))
    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind,
                          np.unique(np.hstack((indnan, indnan - 1,
                                               indnan + 1))),
                          invert=True)]
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size - 1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]),
                    axis=0)
        ind = np.delete(ind, np.where(dx < threshold)[0])
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                    & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])

    return ind
