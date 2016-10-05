import os
import sys
import time
import platform
from datetime import datetime
import pandas as pd
import numpy as np
import pymongo
from sklearn.cross_validation import ShuffleSplit

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
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils
import change_point.hyperparameter_opt.param_sampler as param_sampler

client = pymongo.MongoClient()
db = client["change_point"]
collection = db["random_search"]


class RandomSearch():
    def __init__(self, cmp_class_args, f_metrics, dataset):
        self.cmp_class_args = cmp_class_args
        self.f_metrics = f_metrics
        self.dataset = dataset

        train_path = "{}/change_point/input/{}/dataset.csv".format(base_dir,
                                                                   dataset)
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

    def run(self, model_class, n_iter):
        for run in xrange(n_iter):
            param = param_sampler.sample_param(model_class)
            preprocess_args = param_sampler.sample_preprocess()

            print "model_class={}".format(model_class.__name__)
            print "run {}/{}".format(run + 1, n_iter)
            print "param={}".format(cp_utils.param_pp(param))
            print ("preprocess_args={}".
                   format(cp_utils.param_pp(preprocess_args)))

            if ((not cp_utils.valid_preprocess_args(preprocess_args)) or
                    (not cp_utils.valid_param(param))):
                print "invalid"
                continue

            model = model_class(preprocess_args=preprocess_args, **param)

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
            dic["model_class"] = model_class.__name__
            dic["dataset"] = self.dataset
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


def main():
    dataset = "rosam@land.ufrj.br"
    cmp_class_args = {"win_len": 15}
    f_metrics = [cmp_class.f_half_score, cmp_class.f_1_score,
                 cmp_class.f_2_score, cmp_class.jcc, cmp_class.acc,
                 cmp_class.bacc]

    random_search = RandomSearch(cmp_class_args, f_metrics, dataset)

    random_search.run(SegmentNeighbourhood, 50)
    random_search.run(SlidingWindowsOffline, 50)
    random_search.run(SlidingWindowsOnline, 50)
    random_search.run(GaussianHMM, 50)
    random_search.run(DiscreteHMM, 50)
    random_search.run(BayesianOnline, 50)
    # random_search.run(BayesianOffline, 1)


if __name__ == "__main__":
    main()
