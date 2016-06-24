import time
import copy
import platform
from datetime import datetime
import pandas as pd
import numpy as np
from pymongo import MongoClient
from scipy.stats import uniform
from sklearn.cross_validation import ShuffleSplit
from sklearn.grid_search import ParameterSampler

client = MongoClient()
db = client["change_point"]


class SegmentNeighbourhood():
    def __init__(self, pen):
        self.pen = pen

    def fit(self, df):
        pass

    def predict(self, df):
        pass

    def score(self, df):
        return 0


class RandomSearch():
    """
    - attributes:
        - model_class: model class to be tested
        - param_distr: dictionary used by ParameterSampler
        - df: pandas df with train dataset
        - cv: cross validation iterator
    """

    def __init__(self, model_class, param_distr, train_path):
        """
        - args:
            - model_class:
            - param_distr:
            - train_path: path to train file
        """

        self.model_class = model_class
        self.param_distr = param_distr

        self.df = pd.read_csv(train_path)

        # Every time cv is iterated can generate different results.
        # test_size cannot be equal to 1, but setting near to 1 the same result
        # is achieved.
        self.cv = ShuffleSplit(len(self.df), n_iter=1,
                               test_size=1.0 - np.finfo(float).eps)
        # for train_index, test_index in self.cv:
        #    print("%s %s" % (train_index, test_index))

    def run(self, n_iter):
        params = ParameterSampler(self.param_distr, n_iter=n_iter)
        for param in params:
            model = self.model_class(**param)

            # Iterate through cv iterator accumalating score.
            # In each iteration train model with train set and get score in
            # validation set. The final score will be the mean of scores.
            score, cnt_iter = 0, 0
            fit_time, score_time = 0, 0
            for train_idxs, val_idxs in self.cv:
                cnt_iter += 1

                start_time = time.time()
                model.fit(self.df.iloc[train_idxs])
                fit_time += time.time() - start_time

                start_time = time.time()
                score += model.score(self.df.iloc[val_idxs])
                score_time += time.time() - start_time

            if cnt_iter > 0:
                score /= float(cnt_iter)
                fit_time /= float(cnt_iter)
                score_time /= float(cnt_iter)

            # save results in mongodb
            dic = {}
            dic["params"] = copy.deepcopy(param)
            dic["exec_stats"] = {}
            dic["exec_stats"]["host"] = platform.node()
            dic["exec_stats"]["fit_time"] = fit_time
            dic["exec_stats"]["score_time"] = score_time
            dic["exec_stats"]["score"] = score
            dic["exec_stats"]["insertion_dt_utc"] = datetime.utcnow()
            collection = db[self.model_class.__name__]
            collection.insert(dic)


def main():
    # uniform distribution in [loc, loc + scale]
    param_distr = {"pen": uniform(loc=0, scale=10)}
    random_search = RandomSearch(SegmentNeighbourhood, param_distr,
                                 "./train.csv")
    random_search.run(2)


if __name__ == "__main__":
    main()
