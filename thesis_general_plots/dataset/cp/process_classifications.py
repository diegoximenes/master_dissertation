import os
import sys
import numpy as np
import pandas as pd

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries
from change_point.cp_utils.distribution import hellinger_dist

target_email = "gustavo.santos@tgr.net.br"


def create_dirs(email):
    for dir in ["./plots/", "./plots/per_user/",
                "./plots/per_user/{}".format(email)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def plot(row, dt_cp_list, ts, dt_start, dt_end):
    out_path = ("./plots/per_user/{}/{}_{}_dtstart{}_dtend{}"
                "".format(target_email, row["server"], row["mac"],
                          str(dt_start), str(dt_end)))
    plot_procedures.plot_ts(ts, out_path, dt_cp_list, compress=True,
                            ylim=[-0.05, 1.05])


def write_to_file(l, out_path):
    with open(out_path, "w") as f:
        f.write("samples\n")
        for x in l:
            f.write("{}\n".format(x))


def process():
    create_dirs(target_email)

    cnt_points = 0
    cps_per_ts_samples = []
    middle_seg_len_samples = []
    first_seg_len_samples = []
    last_seg_len_samples = []
    abs_mean_diff_consecutive_segs = []
    hellinger_dist_consecutive_segs = []
    cnt_rows = 0

    df = pd.read_csv("./classifications.csv", sep=";")
    for idx, row in df.iterrows():
        if row["email"] == target_email:
            cnt_rows += 1
            print "cnt_rows={}".format(cnt_rows)
            # print "row={}".format(row)

            # get change points list
            dt_cp_list = []
            if row["change_points"] != "''":
                for strdt in row["change_points"].split(","):
                    dt = dt_procedures.from_js_strdt_to_dt(strdt)
                    dt_cp_list.append(dt)
            dt_cp_list.sort()

            dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
            dt_end = dt_procedures.from_js_strdate_to_dt(row["date_end"])
            in_path = ("../../../input/{}_{}/{}/{}.csv"
                       "".format(dt_start.year, str(dt_start.month).zfill(2),
                                 row["server"], row["mac"]))

            ts = TimeSeries(in_path=in_path, metric="loss", dt_start=dt_start,
                            dt_end=dt_end)

            cnt_points += len(ts.y)
            cps_per_ts_samples.append(len(dt_cp_list))

            # get id_cp_list, first_seg_len, middle_seg_len, last_seg_len
            id_cp_list = []
            i, j, last_cp_i = 0, 0, -1
            while (i < len(ts.x)) and (j < len(dt_cp_list)):
                if ts.x[i] == dt_cp_list[j]:
                    id_cp_list.append(i)
                    if j == 0:
                        first_seg_len_samples.append(i + 1)
                    if j == len(dt_cp_list) - 1:
                        last_seg_len_samples.append(len(ts.x) - i - 1)
                    if last_cp_i != -1:
                        middle_seg_len_samples.append(i - last_cp_i)
                    last_cp_i = i
                    j += 1
                i += 1
            if (j != len(dt_cp_list)):
                print "ERROR"

            # get abs_mean_diff_consecutive_segs and
            # hellinger_dist_consecutive_segments
            segs_list = []
            last_id_cp = -1
            for i in xrange(len(id_cp_list)):
                if (id_cp_list[i] == 0) or (id_cp_list[i] == len(ts.y) - 1):
                    continue
                segs_list.append([last_id_cp + 1, id_cp_list[i]])
                if i == len(id_cp_list) - 1:
                    segs_list.append([id_cp_list[i] + 1, len(ts.y) - 1])
                last_id_cp = id_cp_list[i]
            for i in xrange(1, len(segs_list)):
                l1 = ts.y[segs_list[i - 1][0]:segs_list[i - 1][1] + 1]
                l2 = ts.y[segs_list[i][0]:segs_list[i][1] + 1]

                mean1 = np.mean(l1)
                mean2 = np.mean(l2)
                abs_mean_diff_consecutive_segs.append(abs(mean1 - mean2))

                bins = np.arange(0.0, 1.02, 0.02)
                hellinger_dist_consecutive_segs.append(hellinger_dist(l1, l2,
                                                                      bins))

            plot(row, dt_cp_list, ts, dt_start, dt_end)

    # write_to_file(cps_per_ts_samples, "./plots/distr/cps_per_ts_samples.csv")
    # write_to_file(first_seg_len_samples,
    #               "./plots/distr/first_seg_len_samples.csv")
    # write_to_file(middle_seg_len_samples,
    #               "./plots/distr/middle_seg_len_samples.csv")
    # write_to_file(last_seg_len_samples,
    #               "./plots/distr/last_seg_len_samples.csv")
    # write_to_file(abs_mean_diff_consecutive_segs,
    #               "./plots/distr/abs_mean_diff_consecutive_segs.csv")
    # write_to_file(hellinger_dist_consecutive_segs,
    #               "./plots/distr/hellinger_dist_consecutive_segs.csv")
    #
    # with open("./basic_stats.csv", "w") as f:
    #     f.write("cnt_points\n")
    #     f.write("{}\n".format(cnt_points))


if __name__ == "__main__":
    process()
