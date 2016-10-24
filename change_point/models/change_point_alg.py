import os
import sys
import abc
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils
from utils.time_series import TimeSeries


class ChangePointAlg:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__():
        pass

    @abc.abstractmethod
    def fit():
        pass

    @abc.abstractmethod
    def predict():
        pass

    def score(self, df, cmp_class_args):
        """
        returns one confusion matrix considering all df rows
        """

        conf = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
        cnt = 0
        for idx, row in df.iterrows():
            cnt += 1

            ts = cp_utils.get_ts(row, self.preprocess_args)
            pred = self.predict(ts)
            correct = cp_utils.from_str_to_int_list(row["change_points_ids"])

            print "cnt={}".format(cnt)
            # print "pred={}".format(pred)
            # print "correct={}".format(correct)

            lconf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
            for key in lconf.keys():
                conf[key] += lconf[key]

        return conf

    def plot_all(self, dataset, out_dir_path, cmp_class_args, metric):
        train_path = "{}/change_point/input/{}/dataset.csv".format(base_dir,
                                                                   dataset)

        df = pd.read_csv(train_path)
        cnt = 0
        for idx, row in df.iterrows():
            cnt += 1
            print "cnt={}".format(cnt)

            ts_preprocessed = cp_utils.get_ts(row, self.preprocess_args)
            pred = self.predict(ts_preprocessed)
            correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
            conf = cmp_class.conf_mat(correct, pred, ts_preprocessed,
                                      **cmp_class_args)
            print "pred={}".format(pred)
            print "correct={}".format(correct)
            print "conf={}".format(conf)

            in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
            out_file_name = utils.get_out_file_name(row["server"], row["mac"],
                                                    dt_start, dt_end)
            out_path = "{}/id{}_{}.png".format(out_dir_path, idx,
                                               out_file_name)
            ts_raw = TimeSeries(in_path, metric, dt_start, dt_end)
            self.plot(ts_preprocessed, ts_raw, correct, pred, conf, out_path)

            out_path = "{}/id{}_{}.csv".format(out_dir_path, idx,
                                               out_file_name)
            self.print_cp(ts_raw, pred, out_path)

    @abc.abstractmethod
    def plot():
        pass

    def print_cp(self, ts_raw, pred, out_path):
        with open(out_path, "w") as f:
            f.write("dt_id,dt\n")
            for dt_id, dt in zip(pred, np.asarray(ts_raw.x)[pred]):
                f.write("{},{}\n".format(dt_id, dt))
