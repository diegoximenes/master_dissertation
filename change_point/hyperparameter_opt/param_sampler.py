import os
import sys
from sklearn.grid_search import ParameterSampler
from scipy.stats import uniform, randint

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
from change_point.models.seg_neigh.seg_neigh import SegmentNeighbourhood
from change_point.models.sliding_windows.sliding_windows_online import \
    SlidingWindowsOnline
from change_point.models.sliding_windows.sliding_windows_offline import \
    SlidingWindowsOffline
from change_point.models.bayesian.bayesian_offline import BayesianOffline
from change_point.models.bayesian.bayesian_online import BayesianOnline
from change_point.models.hmm.gaussian_hmm import GaussianHMM
from change_point.models.hmm.discrete_hmm import DiscreteHMM
import change_point.models.bayesian.bayesian_changepoint_detection.\
    offline_changepoint_detection as offcd
import change_point.utils.cmp_win as cmp_win

# uniform: uniform distribution in [loc, loc + scale].
# randint(a, b): generate random in [a, b).
# polyorder is only used in savgol and must be less than win_len.


def sample_scikit(dic):
    for sample in ParameterSampler(dic, n_iter=1):
        return sample


def sample_preprocess():
    preprocess_distr = {"filter_type": ["none", "ma_smoothing"],
                        "win_len": randint(2, 20)}
    return sample_scikit(preprocess_distr)


def sample_param(model_class):
    if model_class == SegmentNeighbourhood:
        return sample_seg_neigh()
    elif model_class == SlidingWindowsOffline:
        return sample_sliding_windows_offline()
    elif model_class == SlidingWindowsOnline:
        return sample_sliding_windows_online()
    elif model_class == BayesianOffline:
        return sample_bayesian_offline()
    elif model_class == BayesianOnline:
        return sample_bayesian_online()
    elif model_class == GaussianHMM:
        return sample_gaussian_hmm()
    elif model_class == DiscreteHMM:
        return sample_discrete_hmm()


def sample_seg_neigh():
    param_distr = {"const_pen": uniform(loc=0, scale=100),
                   "f_pen": ["n_cps", "n_cps * log(n_cps)",
                             "log(n_cps)", "n_cps * sqrt(n_cps)",
                             "sqrt(n_cps)"],
                   "seg_model": ["Exponential", "Normal"],
                   "min_seg_len": randint(2, 30),
                   "max_cps": [20]}
    return sample_scikit(param_distr)


def sample_sliding_windows_offline():
    param_distr = {"win_len": randint(20, 50),
                   "thresh": uniform(loc=0.08, scale=0.7),
                   "min_peak_dist": randint(10, 20),
                   "f_dist": [cmp_win.mean_dist,
                              cmp_win.hellinger_dist],
                   "bin_size_f_dist": [0.05],
                   "min_bin_f_dist": [0.0],
                   "max_bin_f_dist": [1.0]}
    return sample_scikit(param_distr)


def sample_sliding_windows_online():
    param_distr = {"win_len": randint(20, 50),
                   "thresh": uniform(loc=0.2, scale=0.7),
                   "f_dist": [cmp_win.mean_dist,
                              cmp_win.hellinger_dist],
                   "bin_size_f_dist": [0.05],
                   "min_bin_f_dist": [0.0],
                   "max_bin_f_dist": [1.0]}
    return sample_scikit(param_distr)


def sample_bayesian_offline():
    param_distr = {"prior": [offcd.const_prior, offcd.geometric_prior,
                             offcd.neg_binominal_prior],
                   "p": uniform(loc=0.0, scale=1.0),
                   "k": randint(1, 100),
                   "thresh": uniform(loc=0.2, scale=0.7),
                   "min_peak_dist": randint(10, 20)}
    return sample_scikit(param_distr)


def sample_bayesian_online():
    param_distr = {"hazard_lambda": uniform(10, 300),
                   "future_win_len": [10],
                   "thresh": uniform(loc=0.2, scale=0.7),
                   "min_peak_dist": randint(10, 20)}
    return sample_scikit(param_distr)


def sample_gaussian_hmm():
    n = 4
    A = []
    for _ in xrange(n):
        A.append([1.0 / n] * n)
    B = [[0.0, 0.05], [0.05, 0.02], [0.15, 0.05], [0.5, 0.1]]
    pi = [1.0 / n] * n

    param_distr = {"A": [A],
                   "B": [B],
                   "pi": [pi],
                   "win_len": randint(5, 50),
                   "thresh": uniform(loc=0.2, scale=0.9),
                   "min_peak_dist": randint(5, 20)}
    return sample_scikit(param_distr)


def sample_discrete_hmm():
    n = 4
    A = []
    for _ in xrange(n):
        A.append([1.0 / n] * n)
    B = [[0.9, 0.1, 0.0, 0.0, 0.0],
         [0.1, 0.7, 0.1, 0.0, 0.1],
         [0.2, 0.2, 0.5, 0.1, 0.0],
         [0.1, 0.1, 0.4, 0.3, 0.1]]
    pi = [1.0 / n] * n
    obs_bins = [0.01, 0.05, 0.1, 0.3, 1.0]

    param_distr = {"A": [A],
                   "B": [B],
                   "pi": [pi],
                   "obs_bins": [obs_bins],
                   "win_len": randint(5, 50),
                   "thresh": uniform(loc=0.2, scale=0.9),
                   "min_peak_dist": randint(5, 20)}
    return sample_scikit(param_distr)
