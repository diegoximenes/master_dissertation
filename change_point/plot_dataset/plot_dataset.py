import os
import sys
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.utils.cp_utils as cp_utils
import utils.plot_procedures as plot_procedures


def get_cnt_class_per_ts(in_dir):
    ts_cnt = {}
    for dataset in os.listdir(in_dir):
        if dataset != "unsupervised":
            if os.path.isdir("{}/{}".format(in_dir, dataset)):
                df = pd.read_csv("{}/{}/dataset.csv".format(in_dir, dataset))
                for idx, row in df.iterrows():
                    key = (row["server"], row["mac"], row["date_start"],
                           row["date_end"])
                    if key not in ts_cnt:
                        ts_cnt[key] = 0
                    ts_cnt[key] += 1
    return ts_cnt


def plot_dataset():
    utils.create_dirs(["{}/plots/".format(script_dir)])
    in_dir = "{}/change_point/input/".format(base_dir)

    ts_cnt = get_cnt_class_per_ts(in_dir)

    for dataset in os.listdir(in_dir):
        if os.path.isdir("{}/{}".format(in_dir, dataset)) and \
                (dataset != "unsupervised"):
            df = pd.read_csv("{}/{}/dataset.csv".format(in_dir, dataset))
            for idx, row in df.iterrows():
                print "dataset={}, idx={}".format(dataset, idx)

                ts = cp_utils.get_ts(row, {"filter_type": "none"})
                correct = cp_utils.from_str_to_int_list(
                    row["change_points_ids"])

                _, dt_start, dt_end = cp_utils.unpack_pandas_row(row)
                ts_key = (row["server"], row["mac"], row["date_start"],
                          row["date_end"])
                out_file_name = utils.get_out_file_name(row["server"],
                                                        row["mac"],
                                                        dt_start,
                                                        dt_end)
                out_dir = "{}/plots/cnt{}_{}".format(script_dir,
                                                     ts_cnt[ts_key],
                                                     out_file_name)
                out_path = "{}/{}.png".format(out_dir, dataset)
                utils.create_dirs([out_dir])
                plot_procedures.plot_ts(ts, out_path, ylim=[-0.02, 1.02],
                                        dt_axvline=np.asarray(ts.x)[correct],
                                        compress=True)


if __name__ == "__main__":
    plot_dataset()
