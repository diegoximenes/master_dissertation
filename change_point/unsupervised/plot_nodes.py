# TODO: DEPRECATED

import sys
import os
import datetime
import functools

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.read_input as read_input
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries


def plot_per_node(dt_start, dt_end, metric, only_unique_traceroute):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/nodes".format(script_dir),
                       "{}/plots/nodes/{}".format(script_dir, str_dt),
                       "{}/plots/nodes/{}/{}".format(script_dir, str_dt,
                                                     metric)])

    valid_nodes = read_input.get_valid_nodes()
    mac_node = read_input.get_mac_node()

    macs_unique_traceroute = read_input.get_macs_traceroute_filter(dt_start,
                                                                   dt_end,
                                                                   "filtered")

    for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
        if only_unique_traceroute and (mac not in macs_unique_traceroute):
            continue

        if mac_node[mac] in valid_nodes:
            utils.create_dirs(["{}/plots/nodes/{}/{}/{}".
                               format(script_dir, str_dt, metric,
                                      mac_node[mac])])
            out_file_name = utils.get_out_file_name(server, mac, dt_start,
                                                    dt_end)
            out_path = ("{}/plots/nodes/{}/{}/{}/{}.png".
                        format(script_dir, str_dt, metric, mac_node[mac],
                               out_file_name))

            ts = TimeSeries(in_path, metric, dt_start, dt_end)
            ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
            ts_filter.percentile_filter(win_len=13, p=0.5)
            plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
                                            compress=False,
                                            plot_type2="scatter")


def run_sequential(metric, only_unique_traceroute):
    for dt_start, dt_end in utils.iter_dt_range():
        plot_per_node(dt_start, dt_end, metric, only_unique_traceroute)


def run_parallel(metric, only_unique_traceroute):
    dt_ranges = list(utils.iter_dt_range())
    f_plot_per_node = \
        functools.partial(plot_per_node, metric=metric,
                          only_unique_traceroute=only_unique_traceroute)
    utils.parallel_exec(f_plot_per_node, dt_ranges)


def run_single(metric, dt_start, dt_end, only_unique_traceroute):
    plot_per_node(dt_start, dt_end, metric, only_unique_traceroute)


if __name__ == "__main__":
    metric = "latency"
    only_unique_traceroute = True
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(metric, dt_start, dt_end, only_unique_traceroute)
    # run_parallel(metric, only_unique_traceroute)
    # run_sequential(metric, only_unique_traceroute)
