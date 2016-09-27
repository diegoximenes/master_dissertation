import os
import sys
import abc

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.utils.cmp_class as cmp_class


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
        for idx, row in df.iterrows():
            pred = self.predict(row)
            correct = cmp_class.from_str_to_int_list(row["change_points_ids"])
            ts = cmp_class.get_ts(row, self.preprocess_args)
            # print "pred={}".format(pred)
            # print "correct={}".format(correct)

            lconf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
            for key in lconf.keys():
                conf[key] += lconf[key]

        return conf
