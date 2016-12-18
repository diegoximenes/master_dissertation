import os
import sys
import abc
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cmp_class as cmp_class
import change_point.cp_utils.cp_utils as cp_utils
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

            ts = cp_utils.get_ts(row, self.preprocess_args, self.metric)
            pred = self.predict(ts)
            correct = cp_utils.from_str_to_int_list(row["change_points_ids"])

            print "cnt={}".format(cnt)
            # print "pred={}".format(pred)
            # print "correct={}".format(correct)

            lconf = cmp_class.conf_mat(correct, pred, ts, cmp_class.match_id,
                                       **cmp_class_args)
            for key in lconf.keys():
                conf[key] += lconf[key]

        return conf

    def plot_single(self, row, cmp_class_args, dataset, out_path):
        ts_preprocessed = cp_utils.get_ts(row, self.preprocess_args,
                                          self.metric)
        pred = self.predict(ts_preprocessed)
        correct = cp_utils.from_str_to_int_list(row["change_points_ids"])
        conf = cmp_class.conf_mat(correct, pred, ts_preprocessed,
                                  cmp_class.match_id, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        # if is an unsupervised problem, plot the predicted cps in the ts
        if "unsupervised" in dataset:
            pred, correct = correct, pred

        in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)

        out_path = "{}.png".format(out_path)
        ts_raw = TimeSeries(in_path, self.metric, dt_start, dt_end)
        self.plot(ts_preprocessed, ts_raw, correct, pred, conf, out_path)

        out_path = "{}.csv".format(out_path)
        self.print_cp(ts_raw, pred, out_path)

    def plot_all(self, dataset, out_dir_path, cmp_class_args):
        train_path = "{}/change_point/input/{}/dataset.csv".format(base_dir,
                                                                   dataset)

        df = pd.read_csv(train_path)
        cnt = 0
        for idx, row in df.iterrows():
            cnt += 1
            print "cnt={}".format(cnt)

            in_path, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
            out_file_name = utils.get_out_file_name(row["server"],
                                                    row["mac"],
                                                    dt_start, dt_end)
            out_path = "{}/id{}_{}".format(out_dir_path, idx, out_file_name)
            self.plot_single(row, cmp_class_args, dataset, out_path)

    @abc.abstractmethod
    def plot():
        pass

    def print_cp(self, ts_raw, pred, out_path):
        with open(out_path, "w") as f:
            f.write("dt_id,dt\n")
            for dt_id, dt in zip(pred, np.asarray(ts_raw.x)[pred]):
                f.write("{},{}\n".format(dt_id, dt))


def run_parallel(cmp_class_args, preprocess_args, param, metric, run):
    datasets = list(cp_utils.iter_unsupervised_datasets())
    cp_utils.run_parallel(datasets, run, cmp_class_args, preprocess_args,
                          param, metric)


def run_sequential(cmp_class_args, preprocess_args, param, metric, run):
    datasets = list(cp_utils.iter_unsupervised_datasets())
    cp_utils.run_sequential(datasets, run, cmp_class_args, preprocess_args,
                            param, metric)


def run_single(dt_start, dt_end, cmp_class_args, preprocess_args, param,
               metric, run):
    str_dt = utils.get_str_dt(dt_start, dt_end)
    datasets = ["unsupervised/{}".format(str_dt)]
    cp_utils.run_sequential(datasets, run, cmp_class_args, preprocess_args,
                            param, metric)


def run_specific_client(dt_start, dt_end, cmp_class_args, preprocess_args,
                        param, metric, mac, server, model_class, out_path):
    model = model_class(preprocess_args=preprocess_args, metric=metric,
                        **param)
    out_file_name = utils.get_out_file_name(server, mac, dt_start, dt_end)
    out_path = "{}/{}".format(out_path, out_file_name)
    row = {"mac": mac, "server": server, "dt_start": str(dt_start),
           "dt_end": str(dt_end), "change_points_ids": None}
    model.plot_single(row, cmp_class_args, "unsupervised", out_path)
