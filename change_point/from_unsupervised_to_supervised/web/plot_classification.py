import psycopg2
import os
import sys
import datetime
import psycopg2.extras
from math import sqrt
import numpy as np

sys.path.append("../../../utils/")
import plot_procedures
import dt_procedures
from time_series import TimeSeries


target_email = "gabriel.mendonca@tgr.net.br"


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


def hellinger_dist(distr1, distr2):
    dist = 0.0
    for i in xrange(len(distr1)):
        dist += (sqrt(distr1[i]) - sqrt(distr2[i])) ** 2
    dist /= 2.0
    dist = sqrt(dist)
    return dist


def get_distr(l):
    bins = np.arange(0.01, 1.0 + 0.01, 0.01)
    hist = [0] * len(bins)

    for x in l:
        bin = 0
        while bin < len(bins):
            if x <= bins[bin]:
                break
            bin += 1
        hist[bin] += 1

    return np.asarray(hist) / float(np.sum(hist))


def distance(l1, l2):
    distr1 = get_distr(l1)
    distr2 = get_distr(l2)
    return hellinger_dist(distr1, distr2)


def process():
    create_dirs(target_email)

    try:
        conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' "
                                "user='postgres' host='localhost' "
                                "password='admin'")
        conn.autocommit = True
    except:
        print "unable to connect to the database"
        sys.exit(0)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT users.email, time_series.mac, time_series.server, "
                   "time_series.date_start, time_series.date_end, "
                   "change_points.change_points FROM users, time_series, "
                   "change_points WHERE (change_points.id_user = users.id) "
                   "AND (change_points.id_time_series = time_series.id) AND "
                   "(users.email = '{}')".format(target_email))
    cnt_points = 0
    cnt_cps_per_ts_samples = []
    middle_segment_length_samples = []
    first_segment_length_samples = []
    last_segment_length_samples = []
    abs_diff_mean_consecutive_segments = []
    rel_diff_mean_consecutive_segments = []
    hellinger_dist_consecutive_segments = []
    cnt_rows = 0
    for row in cursor.fetchall():
        cnt_rows += 1
        print "cnt_rows={}".format(cnt_rows)
        dt_cp_list = []
        if row["change_points"] != "":
            for strdt in row["change_points"].split(","):
                str_date = strdt.split("T")[0]
                str_time = strdt.split("T")[1].split(".")[0]
                dt = datetime.datetime(int(str_date.split("-")[0]),
                                       int(str_date.split("-")[1]),
                                       int(str_date.split("-")[2]),
                                       int(str_time.split(":")[0]),
                                       int(str_time.split(":")[1]),
                                       int(str_time.split(":")[2]))
                dt_sp = dt_procedures.from_utc_to_sp(dt)
                dt = datetime.datetime(dt_sp.year, dt_sp.month, dt_sp.day,
                                       dt_sp.hour, dt_sp.minute, dt_sp.second)
                dt_cp_list.append(dt)

        in_path = ("../../../input/{}_{}/{}/{}.csv"
                   "".format(str(2016), str(5).zfill(2),
                             row["server"], row["mac"]))

        dt_start = datetime.datetime(int(row["date_start"].split("/")[2]),
                                     int(row["date_start"].split("/")[0]),
                                     int(row["date_start"].split("/")[1]))
        dt_end = datetime.datetime(int(row["date_end"].split("/")[2]),
                                   int(row["date_end"].split("/")[0]),
                                   int(row["date_end"].split("/")[1]))
        ts = TimeSeries(in_path=in_path, metric="loss", dt_start=dt_start,
                        dt_end=dt_end)

        cnt_points += len(ts.y)

        cnt_cps_per_ts_samples.append(len(dt_cp_list))

        id_cp_list = []
        dt_cp_list.sort()
        i, j, last_cp_i = 0, 0, -1
        while (i < len(ts.x)) and (j < len(dt_cp_list)):
            if ts.x[i] == dt_cp_list[j]:
                id_cp_list.append(i)
                if j == 0:
                    first_segment_length_samples.append(i + 1)
                if j == len(dt_cp_list) - 1:
                    last_segment_length_samples.append(len(ts.x) - i - 1)
                if last_cp_i != -1:
                    middle_segment_length_samples.append(i - last_cp_i)
                last_cp_i = i
                j += 1
            i += 1
        if (j != len(dt_cp_list)):
            print "ERROR"

        csum = [0.0] * (len(ts.y) + 1)
        for i in xrange(len(ts.y)):
            csum[i + 1] = csum[i] + ts.y[i]
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
            mean1 = (csum[segs_list[i - 1][1] + 1] - csum[segs_list[i - 1][0]])
            mean1 /= float(segs_list[i - 1][1] - segs_list[i - 1][0] + 1)
            mean2 = (csum[segs_list[i][1] + 1] - csum[segs_list[i][0]])
            mean2 /= float(segs_list[i][1] - segs_list[i][0] + 1)
            abs_diff_mean_consecutive_segments.append(abs(mean1 - mean2))
            if max(mean1, mean2) > 0.0:
                num = min(mean1, mean2)
                den = float(max(mean1, mean2))
                rel_diff_mean_consecutive_segments.append(num / den)
            else:
                rel_diff_mean_consecutive_segments.append(0.0)

            l1 = ts.y[segs_list[i - 1][0]:segs_list[i - 1][1] + 1]
            l2 = ts.y[segs_list[i][0]:segs_list[i][1] + 1]
            hellinger_dist_consecutive_segments.append(distance(l1, l2))

            if np.isclose(distance(l1, l2), 0.0):
                print ""
                print "id_cp_list={}".format(id_cp_list)
                print "l1={}, l2={}".format(l1, l2)
                return

        # plot(row, dt_cp_list, ts, dt_start, dt_end)
    # write_to_file(cnt_cps_per_ts_samples, "./cnt_cps_per_ts_samples.csv")
    # write_to_file(first_segment_length_samples,
    #               "./first_segment_length_samples.csv")
    # write_to_file(middle_segment_length_samples,
    #               "./middle_segment_length_samples.csv")
    # write_to_file(last_segment_length_samples,
    #               "./last_segment_length_samples.csv")
    # write_to_file(abs_diff_mean_consecutive_segments,
    #               "./abs_diff_mean_consecutive_segments.csv")
    # write_to_file(rel_diff_mean_consecutive_segments,
    #               "./rel_diff_mean_consecutive_segments.csv")
    # write_to_file(hellinger_dist_consecutive_segments,
    #               "./hellinger_dist_consecutive_segments.csv")

    with open("./basis_stats.csv", "w") as f:
        f.write("cnt_points\n")
        f.write("{}\n".format(cnt_points))


if __name__ == "__main__":
    process()
