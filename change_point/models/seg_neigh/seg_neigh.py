import os
import sys
import subprocess
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import change_point.models.change_point_alg as change_point_alg


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
        # write ts to file to be consumed
        with open("{}/tmp_ts".format(script_dir), "w") as f:
            for i in xrange(len(ts.y)):
                f.write("{}\n".format(ts.y[i]))

        # c++ executable call
        subprocess.call(["{}/seg_neigh".format(script_dir),
                         "{}/tmp_ts".format(script_dir),
                         "{}/tmp_pred".format(script_dir),
                         str(self.const_pen), self.f_pen, self.seg_model,
                         str(self.min_seg_len), str(self.max_cps)],
                        stdout=open(os.devnull, "w"),
                        stderr=subprocess.STDOUT)

        # R script call
        # subprocess.call(["/usr/bin/Rscript",
        #                  "{}/changepoint.R".format(script_dir),
        #                  "{}/tmp_ts".format(script_dir),
        #                  "{}/tmp_pred".format(script_dir),
        #                  str(self.const_pen), self.seg_model,
        #                  str(self.min_seg_len), str(self.max_cps)],
        #                 stdout=open(os.devnull, "w"),
        #                 stderr=subprocess.STDOUT)

        df = pd.read_csv("{}/tmp_pred".format(script_dir))

        os.remove("{}/tmp_pred".format(script_dir))
        os.remove("{}/tmp_ts".format(script_dir))

        return sorted(df["id"].values)

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        plot_procedures.plot_ts_share_x(ts_raw, ts, out_path, compress=True,
                                        title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        title2="predicted. conf={}".
                                        format(conf),
                                        plot_type2="scatter")


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "ma_smoothing",
                       "win_len": 9}
    param = {"const_pen": 57.120860475387616,
             "f_pen": "n_cps",
             "seg_model": "Exponential",
             "min_seg_len": 15,
             "max_cps": 20}
    metric = "loss"
    dataset = "rosam@land.ufrj.br"

    model = SegmentNeighbourhood(preprocess_args=preprocess_args,
                                 metric=metric, **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/{}".format(script_dir, dataset, metric)])
    out_dir_path = "{}/plots/{}/{}".format(script_dir, dataset, metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()
