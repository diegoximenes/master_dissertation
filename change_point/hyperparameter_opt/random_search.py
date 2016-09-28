import os
import sys
import time
import copy
import platform
from datetime import datetime
import pandas as pd
import numpy as np
import pymongo
from scipy.stats import uniform, randint
from sklearn.cross_validation import ShuffleSplit
from sklearn.grid_search import ParameterSampler

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
from change_point.models.seg_neigh.seg_neigh import SegmentNeighbourhood
from change_point.models.sliding_windows.sliding_windows_online import \
    SlidingWindowsOnline
from change_point.models.sliding_windows.sliding_windows_offline import \
    SlidingWindowsOffline
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cmp_win as cmp_win
import change_point.utils.cp_utils as cp_utils

client = pymongo.MongoClient()
db = client["change_point"]
collection = db["random_search"]


class RandomSearch():
    """
    Attributes:
        model_class:
        param_distr:
        cmp_class_args:
        preprocess_distr:
        f_metrics:
        df:
        cv:
    """

    def __init__(self, cmp_class_args, preprocess_distr, f_metrics,
                 train_path):
        self.cmp_class_args = copy.deepcopy(cmp_class_args)
        self.preprocess_distr = copy.deepcopy(preprocess_distr)
        self.f_metrics = copy.deepcopy(f_metrics)

        self.df = pd.read_csv(train_path)

        # Every time cv is iterated can generate different results.
        # test_size cannot be equal to 1, but setting near to 1 the same result
        # is achieved.
        self.cv = ShuffleSplit(len(self.df), n_iter=1,
                               test_size=1.0 - np.finfo(float).eps)
        # for train_index, test_index in self.cv:
        #    print("%s %s" % (train_index, test_index))

        # create mongo indexes
        for i in xrange(len(self.f_metrics)):
            collection.create_index([("metrics.{}"
                                      "".format(self.f_metrics[i].__name__),
                                      pymongo.ASCENDING)])
        collection.create_index([("conf.tn", pymongo.ASCENDING),
                                 ("conf.fn", pymongo.ASCENDING),
                                 ("conf.fp", pymongo.ASCENDING),
                                 ("conf.tp", pymongo.ASCENDING)])
        collection.create_index([("model_class", pymongo.ASCENDING)])

    def run(self, n_iter):
        ps_param = ParameterSampler(self.param_distr, n_iter=n_iter)
        ps_preprocess = ParameterSampler(self.preprocess_distr, n_iter=n_iter)
        for run, (param, preprocess_args) in enumerate(zip(ps_param,
                                                           ps_preprocess)):
            print "run {}/{}".format(run + 1, n_iter)
            print "param={}".format(cp_utils.param_pp(param))
            print ("preprocess_args={}".
                   format(cp_utils.param_pp(preprocess_args)))

            if ((not cp_utils.valid_preprocess_args(preprocess_args)) or
                    (not cp_utils.valid_param(param))):
                print "invalid"
                continue

            model = self.model_class(preprocess_args=preprocess_args, **param)

            # Iterate through cv iterator accumalating score.
            # In each iteration train model with train set and get score in
            # validation set. The final score will be the mean of scores.
            conf = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
            cnt_iter = 0
            # one score for each score function
            score = [0] * len(self.f_metrics)
            fit_time, score_time = 0, 0
            for train_idxs, val_idxs in self.cv:
                cnt_iter += 1

                start_time = time.time()
                model.fit(self.df.iloc[train_idxs])
                fit_time += time.time() - start_time

                start_time = time.time()
                lconf = model.score(self.df.iloc[val_idxs],
                                    self.cmp_class_args)
                score_time += time.time() - start_time

                # get score for each cost function
                for i in xrange(len(self.f_metrics)):
                    lscore = self.f_metrics[i](lconf)
                    if lscore is None:
                        score[i] = None
                    else:
                        score[i] += lscore

                for key in lconf.keys():
                    conf[key] += lconf[key]

            if cnt_iter > 0:
                for i in xrange(len(self.f_metrics)):
                    if score[i] is not None:
                        score[i] /= float(cnt_iter)

                fit_time /= float(cnt_iter)
                score_time /= float(cnt_iter)

            # save results in mongodb
            dic = {}
            dic["model_class"] = self.model_class.__name__
            dic["params"] = cp_utils.param_pp(param)
            dic["cmp_class_args"] = cp_utils.param_pp(self.cmp_class_args)
            dic["preprocess_args"] = cp_utils.param_pp(preprocess_args)
            dic["conf"] = conf
            dic["exec_stats"] = {}
            dic["exec_stats"]["host"] = platform.node()
            dic["exec_stats"]["fit_time"] = fit_time
            dic["exec_stats"]["score_time"] = score_time
            dic["exec_stats"]["insertion_dt_utc"] = datetime.utcnow()
            dic["metrics"] = {}
            for i in xrange(len(self.f_metrics)):
                dic["metrics"][self.f_metrics[i].__name__] = score[i]
            collection.insert(dic)

    def set_seg_neigh(self):
        self.model_class = SegmentNeighbourhood
        self.param_distr = {"const_pen": uniform(loc=0, scale=100),
                            "f_pen": ["n_cps", "n_cps * log(n_cps)",
                                      "log(n_cps)", "n_cps * sqrt(n_cps)",
                                      "sqrt(n_cps)"],
                            "seg_model": ["Exponential", "Normal"],
                            "min_seg_len": randint(2, 30),
                            "max_cps": [20]}

    def set_sliding_windows_online(self):
        self.model_class = SlidingWindowsOnline
        self.param_distr = {"win_len": randint(20, 50),
                            "thresh": uniform(loc=0.2, scale=0.7),
                            "f_dist": [cmp_win.emd],
                            "bin_size_f_dist": [0.05]}

    def set_sliding_windows_offline(self):
        self.model_class = SlidingWindowsOffline
        self.param_distr = {"win_len": randint(20, 50),
                            "thresh": uniform(loc=0.2, scale=0.7),
                            "min_peak_dist": randint(10, 20),
                            "f_dist": [cmp_win.mean_dist],
                            "bin_size_f_dist": [0.05]}


def main():
    # uniform: uniform distribution in [loc, loc + scale].
    # randint(a, b): generate random in [a, b).
    # polyorder is only used in savgol and must be less than win_len.

    cmp_class_args = {"win_len": 15}
    preprocess_distr = {"filter_type": ["none", "ma_smoothing"],
                        "win_len": randint(2, 20)}
    f_metrics = [cmp_class.f_half_score, cmp_class.f_1_score,
                 cmp_class.f_2_score, cmp_class.jcc, cmp_class.acc,
                 cmp_class.bacc]

    random_search = RandomSearch(cmp_class_args, preprocess_distr,
                                 f_metrics,
                                 "{}/change_point/input/train.csv".
                                 format(base_dir))
    # random_search.set_seg_neigh()
    random_search.set_sliding_windows_offline()
    random_search.run(100000)


if __name__ == "__main__":
    main()
