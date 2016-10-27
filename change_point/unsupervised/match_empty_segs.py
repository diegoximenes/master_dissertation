import os
import sys
import datetime
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries
import change_point.utils.cmp_class as cmp_class


def is_empty_seg(dt_left, dt_right, min_seg_len):
    diff_hours = (dt_right - dt_left).total_seconds() / 60.0 / 60.0
    if diff_hours >= min_seg_len:
        return True
    return False


def print_empty_segs(dt_start, dt_end, metric, min_seg_len=24, plot=False):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/prints/".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt)])

    out_path = "{}/prints/{}/empty_segs_per_mac.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("mac,empty_segs\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts = TimeSeries(in_path=in_path, metric=metric, dt_start=dt_start,
                            dt_end=dt_end)

            if len(ts.x) >= 2:
                axvline_dts = []
                empty_segs = []
                if is_empty_seg(dt_start, ts.x[0], min_seg_len):
                    axvline_dts.append(ts.x[0])
                    empty_segs.append([str(dt_start), str(ts.x[0])])
                for i in xrange(1, len(ts.x)):
                    if is_empty_seg(ts.x[i - 1], ts.x[i], min_seg_len):
                        axvline_dts.append(ts.x[i - 1])
                        axvline_dts.append(ts.x[i])
                        empty_segs.append([str(ts.x[i - 1]), str(ts.x[i])])
                if is_empty_seg(ts.x[-1], dt_end, min_seg_len):
                    axvline_dts.append(ts.x[i - 1])
                    empty_segs.append([str(ts.x[-1]), str(dt_end)])

            f.write("{},\"{}\"\n".format(mac, empty_segs))

            if plot:
                utils.create_dirs(["{}/plots/".format(script_dir),
                                   "{}/plots/empty_segs".format(script_dir),
                                   "{}/plots/empty_segs/{}".format(script_dir,
                                                                   str_dt)])

                out_file_name = utils.get_out_file_name(server, mac, dt_start,
                                                        dt_end)
                out_path = ("{}/plots/empty_segs/{}/{}.png".
                            format(script_dir, str_dt, out_file_name))
                plot_procedures.plot_ts(ts, out_path, dt_axvline=axvline_dts)


def match_empty_segs(dt_start, dt_end, hours_tol=4):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/empty_segs_per_mac.csv".format(script_dir, str_dt)

    mac_emptySegs = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        mac_emptySegs[row["mac"]] = ast.literal_eval(row["empty_segs"])

    for mac in mac_emptySegs:
        for i in xrange(len(mac_emptySegs[mac])):
            for j in xrange(len(mac_emptySegs[mac][i])):
                mac_emptySegs[mac][i][j] = \
                    dt_procedures.from_strdt_to_dt(mac_emptySegs[mac][i][j])

    out_path = "{}/prints/{}/match_empty_segs.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("tp,fp,fn,mac1,mac2,empty_segs1,empty_segs2,matches\n")

        cnt = 0
        for mac1 in mac_emptySegs:
            cnt += 1
            print "cnt={}".format(cnt)

            for mac2 in mac_emptySegs:
                if mac1 != mac2:
                    # only tp, fp, fn are correct with these parameters
                    ts = TimeSeries()
                    conf = cmp_class.conf_mat(mac_emptySegs[mac1],
                                              mac_emptySegs[mac2], ts,
                                              cmp_class.match_seg, hours_tol)

                    f.write("{},{},{},\"{}\",\"{}\",\"{}\",\"{}\"\n".
                            format(conf["tp"], conf["fp"], conf["fn"], mac1,
                                   mac2, mac_emptySegs[mac1],
                                   mac_emptySegs[mac2]))
    utils.sort_csv_file(out_path, ["tp", "fp", "fn"],
                        [False, True, True])


if __name__ == "__main__":
    metric = "latency"

    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 6, 11)
    print_empty_segs(dt_start, dt_end, metric, plot=False)
    match_empty_segs(dt_start, dt_end)

    # for dt_start, dt_end in utils.iter_dt_range():
    #     print_empty_segs(dt_start, dt_end, metric, plot=False)
    #     match_empty_segs(dt_start, dt_end)
