import os
import sys
import subprocess
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import change_point.models.change_point_alg as change_point_alg
import change_point.utils.cp_utils as cp_utils


class SegmentNeighbourhood(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, const_pen, f_pen, seg_model,
                 min_seg_len, max_cps):
        """
        Args:
            preprocess_args:
            metric:
            const_pen: penalization constant to be used in f_pen
            f_pen: penalization function wrt to (c_cps) number of change points
            seg_model: cost function to be used to asess segment homogeneity:
                       "Normal", "Exponential", "MSE"
            min_seg_len: minimum segment length
            max_cps: maximum number of change points in a time series
        """

        self.preprocess_args = preprocess_args
        self.metric = metric

        self.const_pen = const_pen
        self.f_pen = f_pen
        self.seg_model = seg_model
        self.min_seg_len = min_seg_len
        self.max_cps = max_cps

    def fit(self, df):
        pass

    def predict(self, ts):
        popen = subprocess.Popen(["{}/seg_neigh".format(script_dir),
                                  str(self.const_pen),
                                  self.f_pen,
                                  self.seg_model,
                                  str(self.min_seg_len),
                                  str(self.max_cps)],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        str_ts = "{}".format(len(ts.y))
        for v in ts.y:
            str_ts += "\n{}".format(v)
        str_cps, _ = popen.communicate(str_ts)

        cps = map(int, str_cps.split("\n")[:-1])

        return cps

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        plot_procedures.plot_ts_share_x(ts_raw, ts, out_path, compress=False,
                                        title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="predicted. conf={}".
                                        format(conf),
                                        plot_type2="scatter")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = SegmentNeighbourhood(preprocess_args=preprocess_args,
                                 metric=metric, **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/{}".format(script_dir, dataset,
                                               metric)])
    out_dir_path = "{}/plots/{}/{}".format(script_dir, dataset, metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}
    param = {"const_pen": 100,
             "f_pen": "n_cps ^ 2",
             "seg_model": "Normal",
             "min_seg_len": 5,
             "max_cps": 4}
    metric = "latency"

    datasets = ["/unsupervised/dtstart2016-06-21_dtend2016-07-01"]
    # datasets = list(cp_utils.iter_unsupervised_datasets())

    cp_utils.run_sequential(datasets, run, cmp_class_args, preprocess_args,
                            param, metric)
    # cp_utils.run_parallel(datasets, run, cmp_class_args, preprocess_args,
    #                       param, metric)
