import copy
import datetime
import numpy as np
import matplotlib
# matplotlib.use("Agg")
import matplotlib.pyplot as plt


def get_xticks(dt_start, dt_end):
    xticks, xticks_labels = [], []
    for i in range((dt_end - dt_start).days + 2):
        dt = dt_start + datetime.timedelta(days=i)
        xticks.append(dt)
        xticks_labels.append("{}/{}".
                             format(str(dt.day).zfill(2),
                                    str(dt.month).zfill(2)))
    return xticks, xticks_labels


def get_dt_id(ts):
    dt_id = {}
    for id in xrange(len(ts.x)):
        dt_id[ts.x[id]] = id
    return dt_id


def plot_axvline(dt_axvline, dt_id, compress, ax):
    for dt in dt_axvline:
        if compress:
            xvline = dt_id[dt]
        else:
            xvline = dt
        ax.axvline(xvline, color="r", linewidth=2.0)


def plot_ts(ts, out_path, dt_axvline=[], ylabel="", xlabel="", ylim=None, compress=False):
    plt.clf()
    matplotlib.rcParams.update({'font.size': 23})
    plt.gcf().set_size_inches(15, 13)

    if compress:
        xticks = range(0, len(ts.x), 20)
        xticks_labels = copy.deepcopy(xticks)
    else:
        xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)

    if compress:
        dt_id = get_dt_id(ts)

    # plot_axvline(dt_axvline, dt_id, compress, plt)

    plt.grid()
    if ylim is not None:
        plt.ylim(ylim)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    if not compress:
        plt.xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days=1)])
    plt.xticks(xticks, xticks_labels, rotation=45)
    plt.yticks(np.arange(0, 1 + 0.05, 0.1))
    if compress:
        plt.scatter(range(len(ts.x)), ts.y, s=9)
    else:
        plt.scatter(ts.x, ts.y, s=9)
    plt.savefig(out_path)
    plt.close("all")


def get_shared_compress(x1, y1, x2, y2):
    """
    ret_x2 will be a subset of ret_x1: ret_x1[i] == ret_x2[j] iff
    x1[i] == x2[j]

    Args:
        x1:
        y1:
        x2:
        y2:

    Returns:
        ret_x1: = range(len(x1))
        ret_y1: = y1
        ret_x2:
        ret_y2:
    """

    ret_x1, ret_y1 = range(len(x1)), copy.deepcopy(y1)
    ret_x2, ret_y2 = [], []

    i, j = 0, 0
    while (i < len(x1)) and (j < len(x2)):
        if x1[i] == x2[j]:
            ret_x2.append(i)
            ret_y2.append(y2[j])
            i += 1
            j += 1
        elif x1[i] < x2[j]:
            i += 1
        else:  # x1[i] > x2[j]
            j += 1

    return ret_x1, ret_y1, ret_x2, ret_y2


def plot_ts_share_x(ts1, ts2, out_path, compress=False, ylabel1="", ylim1=None,
                    title1="", dt_axvline1=[], plot_type1="scatter",
                    ylabel2="", ylim2=None, title2="", plot_type2="plot",
                    yticks2=None, ytick_labels2=None, dt_axvline2=[],
                    xlabel=""):
    """
    use ts1 as base ts (top plot). Only plot ts2[t] if t is present in ts1
    """

    plt.clf()
    matplotlib.rcParams.update({'font.size': 21})
    f, ax = plt.subplots(2, 1, figsize=(16, 12), sharex="col")

    if compress:
        x1, y1, x2, y2 = get_shared_compress(ts1.x, ts1.y, ts2.x, ts2.y)

        xticks = range(0, len(x1), 100)
        xticks_labels = copy.deepcopy(xticks)

        dt_id1 = get_dt_id(ts1)
        dt_id2 = get_dt_id(ts2)
    else:
        x1, y1 = ts1.x, ts1.y
        x2, y2 = ts2.x, ts2.y

        xticks, xticks_labels = get_xticks(ts1.dt_start, ts1.dt_end)

    plot_axvline(dt_axvline1, dt_id1, compress, ax[0])
    plot_axvline(dt_axvline2, dt_id2, compress, ax[1])

    ax[0].grid()
    ax[0].set_title(title1)
    ax[0].set_ylabel(ylabel1, fontsize=28)
    ax[0].set_xticks(xticks)
    if not compress:
        ax[0].set_xlim([ts1.dt_start, ts1.dt_end + datetime.timedelta(days=1)])
    if ylim1 is not None:
        ax[0].set_ylim(ylim1)
    else:
        ax[0].set_yticks(np.arange(0, 1 + 0.05, 0.05))
        ax[0].set_ylim([-0.02, 1.02])
    if plot_type1 == "plot":
        ax[0].plot(x1, y1)
    else:
        ax[0].scatter(x1, y1, s=9)

    ax[1].grid()
    ax[1].set_title(title2)
    ax[1].set_xlabel(xlabel, fontsize=28)
    ax[1].set_ylabel(ylabel2, fontsize=28)
    ax[1].set_xticks(xticks)
    ax[1].set_xticklabels(xticks_labels, rotation=45)
    if not compress:
        ax[1].set_xlim([ts1.dt_start, ts1.dt_end + datetime.timedelta(days=1)])
    if ylim2 is not None:
        ax[1].set_ylim(ylim2)
    if yticks2 is not None:
        ax[1].set_yticks(yticks2)
    if ytick_labels2 is not None:
        ax[1].set_yticklabels(ytick_labels2)
    if plot_type2 == "plot":
        ax[1].plot(x2, y2)
    else:
        ax[1].scatter(x2, y2, s=9)

    plt.savefig(out_path)
    plt.close("all")


def plotax_ts(ax, ts, plot_raw_data=True, dt_axvline=[], ylabel="", ylim=None):
    """
    DEPRECATED
    """

    for dt in dt_axvline:
        plt.axvline(dt, color="r", linewidth=2.0)

    xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)

    ax.grid()
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticks_labels, rotation="vertical")
    ax.set_xlim([ts.dt_start, ts.dt_end + datetime.timedelta(days=1)])
    if ylim is not None:
        ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)
    if plot_raw_data:
        ax.scatter(ts.raw_x, ts.raw_y, s=9)
    else:
        ax.scatter(ts.x, ts.y, s=9)
