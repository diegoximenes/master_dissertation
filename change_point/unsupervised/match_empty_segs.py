import os
import sys
import datetime
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def create_dirs(date_dir):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/{}".format(script_dir, date_dir),
                "{}/plots/{}/empty_segs".format(script_dir, date_dir),
                "{}/prints/".format(script_dir),
                "{}/prints/{}".format(script_dir, date_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def is_empty_seg(dt_left, dt_right, min_hours):
    diff_hours = (dt_right - dt_left).total_seconds() / 60.0 / 60.0
    if diff_hours >= min_hours:
        return True
    return False


def print_empty_segs(dt_start, dt_end, date_dir, min_hours=24,
                     min_seg_len=20):
    dt_end = dt_end - datetime.timedelta(days=1)
    in_path = ("{}/change_point/input/unsupervised/"
               "unsupervised_dtstart{}_dtend{}/dataset.csv".format(base_dir,
                                                                   dt_start,
                                                                   dt_end))

    out_path = "{}/prints/{}/empty_segs_per_mac.csv".format(script_dir,
                                                            date_dir)
    with open(out_path, "w") as f:
        f.write("mac,empty_segs\n")

        df = pd.read_csv(in_path)
        cnt = 0
        for idx, row in df.iterrows():
            cnt += 1
            print "cnt={}".format(cnt)

            axvline_dts = []
            empty_segs = []
            in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir,
                                                     row["server"], row["mac"])
            ts = TimeSeries(in_path=in_path, metric="loss", dt_start=dt_start,
                            dt_end=dt_end)

            if is_empty_seg(dt_start, ts.x[0], min_hours):
                axvline_dts.append(ts.x[0])
                empty_segs.append((str(dt_start), str(ts.x[0])))
            for i in xrange(1, len(ts.x)):
                if is_empty_seg(ts.x[i - 1], ts.x[i], min_hours):
                    axvline_dts.append(ts.x[i - 1])
                    axvline_dts.append(ts.x[i])
                    empty_segs.append((str(ts.x[i - 1]), str(ts.x[i])))
            if is_empty_seg(ts.x[-1], dt_end, min_hours):
                axvline_dts.append(ts.x[i - 1])
                empty_segs.append((str(ts.x[-1]), str(dt_end)))

            f.write("{},\"{}\"\n".format(row["mac"], empty_segs))

            out_path = ("{}/plots/{}/empty_segs/server{}_mac{}.png".
                        format(script_dir, date_dir, row["server"],
                               row["mac"]))
            plot_procedures.plot_ts(ts, out_path, dt_axvline=axvline_dts)


def dt_close(dt1, dt2, hours_tol=4):
    if dt2 > dt1:
        dt1, dt2 = dt2, dt1
    return ((dt1 - dt2).total_seconds() / 60.0 / 60.0 <= hours_tol)


def match(date_dir):
    in_path = "{}/prints/{}/empty_segs_per_mac.csv".format(script_dir,
                                                           date_dir)

    mac_emptySegs = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac_emptySegs[row["mac"]] = ast.literal_eval(row["empty_segs"])

    out_path = "{}/prints/{}/match_empty_segs_per_mac.csv".format(script_dir,
                                                                  date_dir)
    with open(out_path, "w") as f:
        f.write("cnt_matches,mac1,mac2,empty_segs1,empty_segs2,matches\n")
        for mac1 in mac_emptySegs:
            print "mac1={}".format(mac1)

            for mac2 in mac_emptySegs:
                if mac1 != mac2:
                    matches = []
                    cnt_matches = 0
                    for seg1 in mac_emptySegs[mac1]:
                        for seg2 in mac_emptySegs[mac2]:
                            seg1_dt0 = dt_procedures.from_strdt_to_dt(seg1[0])
                            seg1_dt1 = dt_procedures.from_strdt_to_dt(seg1[1])
                            seg2_dt0 = dt_procedures.from_strdt_to_dt(seg2[0])
                            seg2_dt1 = dt_procedures.from_strdt_to_dt(seg2[1])
                            if (dt_close(seg1_dt0, seg2_dt0) and
                                    dt_close(seg1_dt1, seg2_dt1)):
                                matches.append((seg1, seg2))
                                cnt_matches += 1
                                break
                    f.write("{},{},\"{}\",\"{}\",\"{}\",\"{}\"\n".
                            format(cnt_matches, mac1, mac2,
                                   mac_emptySegs[mac1], mac_emptySegs[mac2],
                                   matches))

    # sort file
    df = pd.read_csv(out_path)
    df_sorted = df.sort(["cnt_matches"], ascending=[False])
    df_sorted.to_csv(out_path, index=False)


if __name__ == "__main__":
    dt_start = datetime.datetime(2015, 12, 1)
    dt_end = datetime.datetime(2016, 1, 1)
    date_dir = "2015_12"

    create_dirs(date_dir)

    print_empty_segs(dt_start, dt_end, date_dir)
    match(date_dir)
