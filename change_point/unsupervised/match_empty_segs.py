import os
import sys
import datetime
import ast
import functools
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.dt_procedures as dt_procedures
import utils.read_input as read_input
from utils.time_series import TimeSeries
import change_point.utils.cmp_class as cmp_class


def from_dt_empty_segs_to_str(empty_segs):
    return map(lambda seg: map(str, seg), empty_segs)


def is_empty_seg(dt_left, dt_right, min_seg_len):
    diff_hours = (dt_right - dt_left).total_seconds() / 60.0 / 60.0
    if diff_hours >= min_seg_len:
        return True
    return False


def print_empty_segs(dt_start, dt_end, metric, min_seg_len, filtered,
                     plot=False):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/prints/".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt),
                       "{}/prints/{}/{}".format(script_dir, str_dt, filtered),
                       "{}/prints/{}/{}/{}".format(script_dir, str_dt,
                                                   filtered, metric)])

    out_path = "{}/prints/{}/{}/{}/empty_segs_per_mac.csv".format(script_dir,
                                                                  str_dt,
                                                                  filtered,
                                                                  metric)
    with open(out_path, "w") as f:
        f.write("server,mac,empty_segs\n")

        target_macs = read_input.get_macs_traceroute_filter(dt_start, dt_end,
                                                            filtered)
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            if mac not in target_macs:
                continue

            ts = TimeSeries(in_path=in_path, metric=metric, dt_start=dt_start,
                            dt_end=dt_end)

            axvline_dts = []
            empty_segs = []
            if len(ts.x) >= 2:
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

            f.write("{},{},\"{}\"\n".format(server, mac, empty_segs))

            if plot:
                utils.create_dirs(["{}/plots/".format(script_dir),
                                   "{}/plots/empty_segs".format(script_dir),
                                   "{}/plots/empty_segs/{}".format(script_dir,
                                                                   str_dt),
                                   "{}/plots/empty_segs/{}/{}".
                                   format(script_dir, str_dt, metric)])

                out_file_name = utils.get_out_file_name(server, mac, dt_start,
                                                        dt_end)
                out_path = ("{}/plots/empty_segs/{}/{}/{}.png".
                            format(script_dir, str_dt, metric, out_file_name))
                plot_procedures.plot_ts(ts, out_path, dt_axvline=axvline_dts)


def match_empty_segs(dt_start, dt_end, metric, hours_tol, filtered):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = ("{}/prints/{}/{}/{}/empty_segs_per_mac.csv".
               format(script_dir, str_dt, filtered, metric))

    macServer_emptySegs = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        macServer_emptySegs[(row["mac"], row["server"])] = \
            ast.literal_eval(row["empty_segs"])

    for tp in macServer_emptySegs:
        for i in xrange(len(macServer_emptySegs[tp])):
            for j in xrange(len(macServer_emptySegs[tp][i])):
                macServer_emptySegs[tp][i][j] = \
                    dt_procedures.from_strdt_to_dt(
                        macServer_emptySegs[tp][i][j])

    out_path = "{}/prints/{}/{}/{}/match_empty_segs.csv".format(script_dir,
                                                                str_dt,
                                                                filtered,
                                                                metric)
    with open(out_path, "w") as f:
        f.write("tp,fp,fn,server1,server2,mac1,mac2,empty_segs1,empty_segs2\n")

        cnt = 0
        for mac1, server1 in macServer_emptySegs:
            cnt += 1
            print "cnt={}".format(cnt)

            for mac2, server2 in macServer_emptySegs:
                if mac1 != mac2:
                    # only tp, fp, fn are correct with these parameters
                    ts = TimeSeries()
                    conf = cmp_class.conf_mat(
                        macServer_emptySegs[(mac1, server1)],
                        macServer_emptySegs[(mac2, server2)], ts,
                        cmp_class.match_seg, hours_tol)

                    empty_segs1 = from_dt_empty_segs_to_str(
                        macServer_emptySegs[(mac1, server1)])
                    empty_segs2 = from_dt_empty_segs_to_str(
                        macServer_emptySegs[(mac2, server2)])

                    f.write("{},{},{},{},{},{},{},\"{}\",\"{}\"\n".
                            format(conf["tp"], conf["fp"], conf["fn"], server1,
                                   server2, mac1, mac2, empty_segs1,
                                   empty_segs2))
    utils.sort_csv_file(out_path, ["tp", "fp", "fn"],
                        [False, True, True])


def run_parallel(metric, min_seg_len, filtered):
    dt_ranges = list(utils.iter_dt_range())
    fp_print_empty_segs = functools.partial(print_empty_segs,
                                            metric=metric,
                                            min_seg_len=min_seg_len,
                                            filtered=filtered,
                                            plot=False)
    utils.parallel_exec(fp_print_empty_segs, dt_ranges)
    fp_match_empty_segs = functools.partial(match_empty_segs,
                                            metric=metric,
                                            hours_tol=hours_tol,
                                            filtered=filtered)
    utils.parallel_exec(fp_match_empty_segs, dt_ranges)


def run_sequential(metric, min_seg_len, filtered, hours_tol):
    for dt_start, dt_end in utils.iter_dt_range():
        print_empty_segs(dt_start, dt_end, metric, min_seg_len, filtered,
                         plot=False)
        match_empty_segs(dt_start, dt_end, metric, hours_tol, filtered)


def run_single(metric, min_seg_len, filtered, hours_tol, dt_start, dt_end):
    print_empty_segs(dt_start, dt_end, metric, min_seg_len, filtered,
                     plot=False)
    match_empty_segs(dt_start, dt_end, metric, hours_tol, filtered)


if __name__ == "__main__":
    metric = "latency"
    min_seg_len = 24
    hours_tol = 4
    filtered = "filtered"

    dt_start = datetime.datetime(2016, 6, 11)
    dt_end = datetime.datetime(2016, 6, 21)

    run_single(metric, min_seg_len, filtered, hours_tol, dt_start, dt_end)
    # run_parallel(metric, min_seg_len, filtered, hours_tol)
    # run_sequential(metric, min_seg_len, filtered, hours_tol)
