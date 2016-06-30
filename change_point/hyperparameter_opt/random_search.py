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
import change_point.utils.cmp_class as cmp_class

client = pymongo.MongoClient()
db = client["change_point_random_search"]


class RandomSearch():
    """
    Attributes:
        model_class: model class to be tested
        param_distr: dictionary used by ParameterSampler
        df: pandas df with train dataset
        cv: cross validation iterator
    """

    def __init__(self, model_class, param_distr, cmp_class_args,
                 preprocess_distr, f_cost, train_path):
        """
        Args:
            model_class:
            param_distr:
            train_path: path to train file
        """

        self.model_class = model_class
        self.param_distr = copy.deepcopy(param_distr)
        self.cmp_class_args = copy.deepcopy(cmp_class_args)
        self.preprocess_distr = copy.deepcopy(preprocess_distr)
        self.f_cost = f_cost

        self.df = pd.read_csv(train_path)

        # Every time cv is iterated can generate different results.
        # test_size cannot be equal to 1, but setting near to 1 the same result
        # is achieved.
        self.cv = ShuffleSplit(len(self.df), n_iter=1,
                               test_size=1.0 - np.finfo(float).eps)
        # for train_index, test_index in self.cv:
        #    print("%s %s" % (train_index, test_index))

        collection = db[self.model_class.__name__]
        collection.create_index([("score", pymongo.ASCENDING),
                                 ("f_cost", pymongo.ASCENDING)])

    def run(self, n_iter):
        ps_param = ParameterSampler(self.param_distr, n_iter=n_iter)
        ps_preprocess = ParameterSampler(self.preprocess_distr, n_iter=n_iter)
        for run, (param, preprocess_args) in enumerate(zip(ps_param,
                                                           ps_preprocess)):
            print "run {}/{}".format(run + 1, n_iter)
            print "param={}".format(param)
            print "preprocess_args={}".format(preprocess_args)

            if ((not cmp_class.valid_preprocess_args(preprocess_args)) or
                    (not cmp_class.valid_param(param))):
                print "invalid"
                continue

            model = self.model_class(preprocess_args=preprocess_args, **param)

            # Iterate through cv iterator accumalating score.
            # In each iteration train model with train set and get score in
            # validation set. The final score will be the mean of scores.
            conf = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
            score, cnt_iter = 0, 0
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

                score += self.f_cost(lconf)
                for key in lconf.keys():
                    conf[key] += lconf[key]

            if cnt_iter > 0:
                score /= float(cnt_iter)
                fit_time /= float(cnt_iter)
                score_time /= float(cnt_iter)

            # save results in mongodb
            dic = {}
            dic["params"] = param
            dic["cmp_class_args"] = self.cmp_class_args
            dic["preprocess_args"] = preprocess_args
            dic["f_cost"] = self.f_cost.__name__
            dic["score"] = score
            dic["conf"] = conf
            dic["exec_stats"] = {}
            dic["exec_stats"]["host"] = platform.node()
            dic["exec_stats"]["fit_time"] = fit_time
            dic["exec_stats"]["score_time"] = score_time
            dic["exec_stats"]["insertion_dt_utc"] = datetime.utcnow()
            collection = db[self.model_class.__name__]
            collection.insert(dic)


def main():
    cmp_class_args = {"win_len": 10}
    preprocess_distr = {"filter_type": ["none", "ma_smoothing",
                                        "median_filter"],
                        "win_len": randint(2, 10)}
    # uniform distribution in [loc, loc + scale]
    param_distr = {"const_pen": uniform(loc=0, scale=1000),
                   "f_pen": ["n_cps", "n_cps^2", "n_cps * sqrt(n_cps)"],
                   "distr_type": ["Normal", "Exponential"],
                   "min_seg_len": randint(2, 15),
                   "max_cps": [20]}
    random_search = RandomSearch(SegmentNeighbourhood, param_distr,
                                 cmp_class_args, preprocess_distr,
                                 cmp_class.f1_score,
                                 "{}/change_point/input/train.csv".
                                 format(base_dir))
    random_search.run(10000)


if __name__ == "__main__":
    main()
