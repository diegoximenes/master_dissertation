import os
import sys
import datetime
import functools

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import utils.read_input as read_input
from utils.time_series import TimeSeries
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


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


def run_parallel(metric, min_seg_len, filtered):
    dt_ranges = list(utils.iter_dt_range())
    fp_print_empty_segs = functools.partial(print_empty_segs,
                                            metric=metric,
                                            min_seg_len=min_seg_len,
                                            filtered=filtered,
                                            plot=False)
    utils.parallel_exec(fp_print_empty_segs, dt_ranges)

    fp_print_per_name = functools.partial(unsupervised_utils.print_per_name,
                                          metric=metric,
                                          file_name="empty_segs_per_mac.csv")
    utils.parallel_exec(fp_print_per_name, dt_ranges)

    fp_print_per_path = functools.partial(unsupervised_utils.print_per_path,
                                          metric=metric,
                                          file_name="empty_segs_per_mac.csv")
    utils.parallel_exec(fp_print_per_path, dt_ranges)


def run_sequential(metric, min_seg_len, filtered, hours_tol):
    for dt_start, dt_end in utils.iter_dt_range():
        print_empty_segs(dt_start, dt_end, metric, min_seg_len, filtered,
                         plot=False)
        unsupervised_utils.print_per_name(dt_start, dt_end, metric,
                                          "empty_segs_per_mac.csv")
        unsupervised_utils.print_per_path(dt_start, dt_end, metric,
                                          "empty_segs_per_mac.csv")


def run_single(metric, min_seg_len, filtered, hours_tol, dt_start, dt_end):
    print_empty_segs(dt_start, dt_end, metric, min_seg_len, filtered,
                     plot=False)
    unsupervised_utils.print_per_name(dt_start, dt_end, metric,
                                      "empty_segs_per_mac.csv")
    unsupervised_utils.print_per_path(dt_start, dt_end, metric,
                                      "empty_segs_per_mac.csv")


if __name__ == "__main__":
    metric = "latency"
    min_seg_len = 24
    hours_tol = 4
    filtered = "filtered"

    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(metric, min_seg_len, filtered, hours_tol, dt_start, dt_end)
    # run_parallel(metric, min_seg_len, filtered, hours_tol)
    # run_sequential(metric, min_seg_len, filtered, hours_tol)
