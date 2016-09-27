import os
import sys
import subprocess
import pandas as pd
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries
import change_point.utils.cmp_class as cmp_class
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

    def predict(self, row):
        ts = cmp_class.get_ts(row, self.preprocess_args)

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

    seg_neigh = SegmentNeighbourhood(preprocess_args=preprocess_args, **param)
    train_path = "{}/change_point/input/train.csv".format(base_dir)

    create_dirs()

    df = pd.read_csv(train_path)
    cnt = 0
    for idx, row in df.iterrows():
        cnt += 1
        print "cnt={}".format(cnt)

        pred = seg_neigh.predict(row)
        correct = cmp_class.from_str_to_int_list(row["change_points_ids"])
        ts = cmp_class.get_ts(row, preprocess_args)
        conf = cmp_class.conf_mat(correct, pred, ts, **cmp_class_args)
        print "pred={}".format(pred)
        print "correct={}".format(correct)
        print "conf={}".format(conf)

        in_path, dt_start, dt_end = cmp_class.unpack_pandas_row(row)
        out_path = ("{}/plots/server{}_mac{}_dtstart{}_dtend{}.png".
                    format(script_dir, row["server"], row["mac"], dt_start,
                           dt_end))
        ts1 = TimeSeries(in_path, "loss", dt_start, dt_end)
        ts2 = TimeSeries(in_path, "loss", dt_start, dt_end)
        cmp_class.preprocess(ts2, preprocess_args)
        plot_procedures.plot_ts_share_x(ts1, ts2, out_path, compress=True,
                                        title1="correct",
                                        dt_axvline1=np.asarray(ts.x)[correct],
                                        dt_axvline2=np.asarray(ts.x)[pred],
                                        ylim2=[-0.02, 1.02],
                                        yticks2=np.arange(0, 1.05, 0.05),
                                        title2="predicted: conf={}".
                                        format(conf),
                                        plot_type2="scatter")

if __name__ == "__main__":
    main()
