import sys
import os
import datetime

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
import utils.utils as utils
from utils.time_series import TimeSeries


def plot(dt_start, dt_end, metric):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)
    utils.create_dirs(["{}/{}".format(script_dir, str_dt),
                       "{}/{}/{}".format(script_dir, str_dt, metric)])
    for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
        out_file_name = utils.get_out_file_name(server, mac, dt_start, dt_end)
        out_path = "{}/{}/{}/{}.png".format(script_dir, str_dt, metric,
                                            out_file_name)

        # comparison between not filtered and filtered
        ts = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter = TimeSeries(in_path, metric, dt_start, dt_end)
        ts_filter.percentile_filter(win_len=5, p=0.5)

        # if len(ts_filter.y) > 100:
        #     plot_procedures.plot_stl_decomposition(ts_filter,
        #                                            "median_filtered",
        #                                            out_path)

        # comparison between with cross traffic and without
        # ts = TimeSeries(in_path, metric, dt_start, dt_end)
        # ts.percentile_filter(win_len=13, p=0.5)
        # ts_filter = TimeSeries(in_path, metric, dt_start, dt_end,
        #                        cross_traffic_thresh=0)
        # ts_filter.percentile_filter(win_len=13, p=0.5)

        # plot_procedures.plot_ts_share_x(ts, ts_filter, out_path,
        #                                 compress=True,
        #                                 plot_type2="scatter",
        #                                 title1="raw",
        #                                 title2="median filtered",
        #                                 default_ylabel=True,
        #                                 xlabel="$i$")

        ylabel = plot_procedures.get_default_ylabel(ts)
        plot_procedures.plot_ts(ts_filter, out_path,
                                ylabel=ylabel,
                                compress=False,
                                title="median filtered")


if __name__ == "__main__":
    metric = "loss"
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)
    plot(dt_start, dt_end, metric)
