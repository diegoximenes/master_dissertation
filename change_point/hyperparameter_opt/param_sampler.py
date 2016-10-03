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
        sampler_class = SegNeighSampler
    elif model_class == SlidingWindowsOffline:
        sampler_class = SlidingWindowsOfflineSampler
    elif model_class == SlidingWindowsOnline:
        sampler_class = SlidingWindowsOnlineSampler
    elif model_class == BayesianOffline:
        sampler_class = BayesianOfflineSampler
    elif model_class == BayesianOnline:
        sampler_class = BayesianOnlineSampler
    elif model_class == GaussianHMM:
        sampler_class = GaussianHMMSampler
    elif model_class == DiscreteHMM:
        sampler_class = DiscreteHMMSampler
    sampler = sampler_class()
    return sampler.sample()


class SegNeighSampler:
    def sample(self):
        param_distr = {"const_pen": uniform(loc=0, scale=100),
                       "f_pen": ["n_cps", "n_cps * log(n_cps)",
                                 "log(n_cps)", "n_cps * sqrt(n_cps)",
                                 "sqrt(n_cps)"],
                       "seg_model": ["Exponential", "Normal"],
                       "min_seg_len": randint(2, 30),
                       "max_cps": [20]}
        return sample_scikit(param_distr)


class SlidingWindowsOfflineSampler:
    def sample(self):
        param_distr = {"win_len": randint(20, 50),
                       "thresh": uniform(loc=0.08, scale=0.7),
                       "min_peak_dist": randint(10, 20),
                       "f_dist": [cmp_win.mean_dist,
                                  cmp_win.hellinger_dist],
                       "bin_size_f_dist": [0.05],
                       "min_bin_f_dist": [0.0],
                       "max_bin_f_dist": [1.0]}
        return sample_scikit(param_distr)


class SlidingWindowsOnlineSampler:
    def sample(self):
        param_distr = {"win_len": randint(20, 50),
                       "thresh": uniform(loc=0.2, scale=0.7),
                       "f_dist": [cmp_win.mean_dist,
                                  cmp_win.hellinger_dist],
                       "bin_size_f_dist": [0.05],
                       "min_bin_f_dist": [0.0],
                       "max_bin_f_dist": [1.0]}
        return sample_scikit(param_distr)


class BayesianOfflineSampler:
    def sample(self):
        param_distr = {"prior": [offcd.const_prior, offcd.geometric_prior,
                                 offcd.neg_binominal_prior],
                       "p": uniform(loc=0.0, scale=1.0),
                       "k": randint(1, 100),
                       "thresh": uniform(loc=0.2, scale=0.7),
                       "min_peak_dist": randint(10, 20)}
        return sample_scikit(param_distr)


class BayesianOnlineSampler:
    def sample(self):
        param_distr = {"hazard_lambda": uniform(10, 300),
                       "future_win_len": [10],
                       "thresh": uniform(loc=0.2, scale=0.7),
                       "min_peak_dist": randint(10, 20)}
        return sample_scikit(param_distr)


class HMMSampler():
    def sample_row(self, n):
        row = []
        psum = 0.0
        for _ in xrange(n - 1):
            row.append(uniform(loc=0.0, scale=1.0 - psum).rvs())
            psum += row[-1]
        row.append(1.0 - psum)
        return row

    def sample_fully(self, n):
        A = []
        for _ in xrange(n):
            A.append(self.sample_row(n))
        return A

    def sample_left_right(self, n):
        A = []
        for i in xrange(n):
            A.append([0.0] * n)
            if i == n - 1:
                A[i][i] = 1.0
            else:
                p_stay = uniform(loc=0.0, scale=1.0).rvs()
                A[i][i] = p_stay
                A[i][i + 1] = 1.0 - p_stay
        return A


class GaussianHMMSampler(HMMSampler):
    def sample_predefined(self):
        n = 4
        A = []
        for _ in xrange(n):
            A.append([1.0 / n] * n)
        B = [[0.0, 0.05], [0.05, 0.02], [0.15, 0.05], [0.5, 0.1]]
        pi = [1.0 / n] * n
        return A, B, pi

    def sample_B(self, n):
        B = []
        for _ in xrange(n):
            mean = uniform(loc=0.0, scale=1.0).rvs()
            var = uniform(0.0, scale=0.1).rvs()
            B.append([mean, var])
        return B

    def sample(self):
        sample_types = ["predefined", "random"]
        sample_type = sample_types[randint(0, len(sample_types)).rvs()]
        if sample_type == "predefined":
            A, B, pi = self.sample_predefined()
            type_name = "predefined"
        else:
            structure_types = [self.sample_fully, self.sample_left_right]
            structure_type = structure_types[
                randint(0, len(structure_types)).rvs()]

            n = randint(2, 20).rvs()
            A = structure_type(n)
            B = self.sample_B(n)
            pi = self.sample_row(n)

            type_name = structure_type.__name__.split("sample_")[1]

        param_distr = {"graph_structure_type": [type_name],
                       "A": [A],
                       "B": [B],
                       "pi": [pi],
                       "win_len": randint(5, 50),
                       "thresh": uniform(loc=0.2, scale=0.9),
                       "min_peak_dist": randint(5, 20)}
        return sample_scikit(param_distr)


class DiscreteHMMSampler(HMMSampler):
    def sample_predefined(self):
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
        return A, B, pi, obs_bins

    def sample_B(self, n, m):
        B = []
        for _ in xrange(n):
            B.append(self.sample_row(m))
        return B

    def sample_obs_bins(self, m):
        obs_bins = [0.01, 0.05, 0.1, 0.3, 1.0]
        return obs_bins

    def sample(self):
        sample_types = ["predefined", "random"]
        sample_type = sample_types[randint(0, len(sample_types)).rvs()]
        if sample_type == "predefined":
            A, B, pi, obs_bins = self.sample_predefined()
            type_name = "predefined"
        else:
            structure_types = [self.sample_fully, self.sample_left_right]
            structure_type = structure_types[
                randint(0, len(structure_types)).rvs()]

            n = randint(2, 20).rvs()
            m = 5  # number of bins in obs distribution
            A = structure_type(n)
            B = self.sample_B(n, m)
            pi = self.sample_row(n)
            obs_bins = self.sample_obs_bins(m)

            type_name = structure_type.__name__.split("sample_")[1]

        param_distr = {"graph_structure_type": [type_name],
                       "A": [A],
                       "B": [B],
                       "pi": [pi],
                       "obs_bins": [obs_bins],
                       "win_len": randint(5, 50),
                       "thresh": uniform(loc=0.2, scale=0.9),
                       "min_peak_dist": randint(5, 20)}
        return sample_scikit(param_distr)
