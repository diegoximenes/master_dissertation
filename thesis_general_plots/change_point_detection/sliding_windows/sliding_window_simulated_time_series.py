import sys
import os
import numpy as np

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries
import change_point.cp_utils.cmp_win as cmp_win


def simulate():
    ts_len = 1000
    l1 = np.random.normal(1, 0.2, ts_len)
    l2 = np.random.normal(5, 0.2, ts_len)
    l = np.append(l1, l2)

    ts = TimeSeries(compressed=True)
    ts.x = range(1, len(l) + 1)
    ts.y = l

    return ts


def sliding_window(ts):
    ts_dist = TimeSeries(compressed=True)

    win_len = 100
    for i in xrange(win_len, len(ts.y) - win_len + 1):
        dist = cmp_win.hellinger_dist(ts.y[i - win_len:i],
                                      ts.y[i:i + win_len],
                                      bins=np.arange(0.02, 10.02, 0.02))
        ts_dist.x.append(ts.x[i])
        ts_dist.y.append(dist)

    plot_procedures.plot_ts_share_x(ts,
                                    ts_dist,
                                    "./sliding_window_toy_example.png",
                                    compress=True,
                                    plot_type1="plot",
                                    ylim1=[0, max(ts.y)],
                                    ylabel1="$y_{i}$",
                                    ylabel2="$H_{i}$",
                                    xlabel="$i$")

if __name__ == "__main__":
    ts = simulate()
    sliding_window(ts)
