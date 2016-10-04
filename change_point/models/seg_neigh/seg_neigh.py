import os
import sys
import subprocess
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import change_point.models.change_point_alg as change_point_alg

script_dir = os.path.join(os.path.dirname(__file__), ".")


class SegmentNeighbourhood(change_point_alg.ChangePointAlg):
    def __init__(self, preprocess_args, const_pen, f_pen, seg_model,
                 min_seg_len, max_cps):
        self.preprocess_args = preprocess_args
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
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0, 1.05, 0.05),
                                        title2="predicted. conf={}".
                                        format(conf),
                                        plot_type2="scatter")


def create_dirs():
    for dir in ["{}/plots/".format(script_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def main():
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "ma_smoothing",
                       "win_len": 15}
    param = {"const_pen": 86.81489011349758,
             "f_pen": "n_cps",
             "seg_model": "Normal",
             "min_seg_len": 21,
             "max_cps": 20}

    model = SegmentNeighbourhood(preprocess_args=preprocess_args, **param)

    create_dirs()
    train_path = "{}/change_point/input/train.csv".format(base_dir)
    out_dir_path = "{}/plots/".format(script_dir)
    model.plot_all(train_path, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    main()
