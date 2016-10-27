import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cp_utils as cp_utils


def cmp_datasets():
    cmp_class_args = {"win_len": 15}
    f_metrics = [cmp_class.f_half_score, cmp_class.f_1_score,
                 cmp_class.f_2_score, cmp_class.jcc, cmp_class.acc,
                 cmp_class.bacc]

    in_dir = "{}/change_point/input/".format(base_dir)

    datasets = []
    for dataset in os.listdir(in_dir):
        if os.path.isdir("{}/{}".format(in_dir, dataset)):
            datasets.append(dataset)

    with open("{}/cmp_datasets.csv".format(script_dir), "w") as f:
        # write header
        f.write("dataset_ground_truth,dataset_other,cnt_compared_ts,"
                "tp,tn,fp,fn")
        for f_metric in f_metrics:
            f.write(",{}".format(f_metric.__name__))
        f.write("\n")

        for dataset1 in datasets:
            for dataset2 in datasets:
                if ((dataset1 != dataset2) and (dataset1 != "unsupervised") and
                        (dataset2 != "unsupervised")):
                    print "dataset1={}, dataset2={}".format(dataset1, dataset2)

                    df1 = pd.read_csv("{}/{}/dataset.csv".format(in_dir,
                                                                 dataset1))
                    df2 = pd.read_csv("{}/{}/dataset.csv".format(in_dir,
                                                                 dataset2))

                    conf = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
                    cnt_compared_ts = 0

                    for idx, row in df1.iterrows():
                        query = ((df2["mac"] == row["mac"]) &
                                 (df2["server"] == row["server"]) &
                                 (df2["dt_start"] == row["dt_start"]) &
                                 (df2["dt_end"] == row["dt_end"]))
                        df_intersec = df2[query]

                        # df_intersec must have 0 or 1 row
                        if df_intersec.shape[0] == 1:
                            cnt_compared_ts += 1

                            ts = cp_utils.get_ts(row, {"filter_type": "none"},
                                                 "loss")
                            correct = cp_utils.from_str_to_int_list(
                                row["change_points_ids"])
                            pred = cp_utils.from_str_to_int_list(
                                df_intersec.iloc[0]["change_points_ids"])

                            lconf = cmp_class.conf_mat(correct, pred, ts,
                                                       cmp_class.match_id,
                                                       **cmp_class_args)
                            for key in lconf.keys():
                                conf[key] += lconf[key]

                    line = "{},{},{}" + ",{}" * 4
                    line = line.format(dataset1, dataset2, cnt_compared_ts,
                                       conf["tp"], conf["tn"], conf["fp"],
                                       conf["fn"])
                    for f_metric in f_metrics:
                        line += ",{}".format(f_metric(conf))
                    line += "\n"
                    f.write(line)


if __name__ == "__main__":
    cmp_datasets()
