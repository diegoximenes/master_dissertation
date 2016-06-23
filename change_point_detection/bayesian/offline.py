import os
import sys
import datetime
import numpy as np

import bayesian_changepoint_detection.offline_changepoint_detection as offcd
from functools import partial

sys.path.append("../../import_scripts/")
import plot_procedures
import time_series
from time_series import TimeSeries

# PARAMETERS
metric = "loss"


def get_change_points(in_path, out_path, dt_start, dt_end):
    ts = TimeSeries(in_path, metric, dt_start, dt_end)

    data = np.asarray(ts.raw_y)
    if len(data) == 0:
        return

    q, p, pcp = (offcd.offline_changepoint_detection(
        data, partial(offcd.const_prior, l=len(data) + 1),
        offcd.gaussian_obs_log_likelihood, truncate=-40))

    prob_list = np.exp(pcp).sum(0)

    ts_dist = time_series.dist_ts(ts)
    for i in xrange(len(ts.x) - 1):
        ts_dist.x.append(ts.x[i])
        ts_dist.y.append(prob_list[i])
    ts_dist.set_dt_mean()

    plot_procedures.plot_ts_share_x(ts, ts_dist, "{}.png".format(out_path),
                                    ylabel1=metric, ylabel2="p",
                                    ylim2=[-0.02, 1.02], compress=True)


def get_datetime(strdate):
    day = int(strdate.split("-")[1])
    month = int(strdate.split("-")[0])
    year = int(strdate.split("-")[2])
    return datetime.datetime(year, month, day)


def create_dirs():
    for dir in ["./plots"]:
        if not os.path.exists(dir):
            os.makedirs("./plots/")


def process():
    targets = [["64:66:B3:4F:FE:CE", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:7B:9B:B8", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:7B:A4:1C", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:50:00:1C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:00:3C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:00:30", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:50:06:82", "NHODTCSRV04", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:9E:DE", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:A6:A9:16", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"],
               ["64:66:B3:A6:AE:76", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:B3:B0", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:BC:D8", "SJCDTCSRV01", "05-11-2016",
                "05-20-2016"],
               ["64:66:B3:A6:A0:78", "AMRDTCPEV01", "05-01-2016",
                "05-10-2016"]]

    for tp in targets:
        print tp
        mac, server, date_start, date_end = tp[0], tp[1], tp[2], tp[3]
        dt_start = get_datetime(date_start)
        dt_end = get_datetime(date_end)
        date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
        in_path = "../input/{}/{}/{}.csv".format(date_dir, server, mac)
        out_path = "./plots/server{}_mac{}_datestart{}_dateend{}".format(
            server, mac, date_start, date_end)

        create_dirs()
        get_change_points(in_path, out_path, dt_start, dt_end)

process()
