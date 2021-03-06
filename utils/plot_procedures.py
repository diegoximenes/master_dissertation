import copy
import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def get_default_yticks(ts):
    if ts.metric == "loss":
        return np.arange(0.0, 1.0 + 0.1, 0.1)


def get_default_ylabel(ts):
    if ts.metric == "loss":
        return "loss fraction"
    elif ts.metric == "latency":
        return "RTT (ms)"
    elif ts.metric == "throughput_up":
        return "throughput up (bps)"


def get_default_xlabel(compress):
    if compress:
        return "$i$"
    return "month/day/year"


def get_default_xtick_rotation(compress):
    if compress:
        return 45
    return 0


def update_title(title, ts):
    if ts.metric:
        title += " metric={}".format(ts.metric)
    if ts.filters:
        title += " filters={}".format(ts.filters)
    return title


def get_xticks(dt_start, dt_end):
    """
    daily xticks of [dt_start, dt_end]
    """
    xticks, xticks_labels = [], []
    for i in range((dt_end - dt_start).days + 1):
        dt = dt_start + datetime.timedelta(days=i)
        xticks.append(dt)
        if i % 2 == 0:
            xticks_labels.append("{}/{}/{}".
                                 format(str(dt.month).zfill(2),
                                        str(dt.day).zfill(2),
                                        str(dt.year % 100)))
        else:
            xticks_labels.append("")
    return xticks, xticks_labels


def get_dt_id(ts):
    dt_id = {}
    for id in xrange(len(ts.x)):
        dt_id[ts.x[id]] = id
    return dt_id


def plot_axvline(ts, dt_axvline, compress, ax):
    if compress:
        dt_id = get_dt_id(ts)
    for dt in dt_axvline:
        if compress:
            xvline = dt_id[dt]
        else:
            xvline = dt
        ax.axvline(xvline, color="r", linewidth=2.0)


def plot_ts(ts, out_path, dt_axvline=[], ylabel=None, xlabel=None, ylim=None,
            compress=False, title=""):
    """
    if compress is true than ts.y must not have None
    """

    plt.clf()
    matplotlib.rcParams.update({'font.size': 26})
    if not compress:
        matplotlib.rcParams.update({'xtick.major.pad': 15})
    plt.gcf().set_size_inches(17, 12)

    if compress:
        xticks = range(0, len(ts.x), 50)
        xticks_labels = copy.deepcopy(xticks)
    else:
        xticks, xticks_labels = get_xticks(ts.dt_start, ts.dt_end)

    plot_axvline(ts, dt_axvline, compress, plt)

    if not title:
        title = update_title("", ts)

    plt.grid()
    plt.title(title)

    if ylabel is None:
        ylabel = get_default_ylabel(ts)
    if xlabel is None:
        xlabel = get_default_xlabel(compress)

    plt.ylabel(ylabel)

    if ts.metric == "loss":
        plt.ylim([-0.02, 1.02])
        plt.yticks(np.arange(0, 1 + 0.05, 0.05))
    if ylim is not None:
        plt.ylim(ylim)

    plt.xlabel(xlabel)
    if not compress:
        plt.xlim([ts.dt_start, ts.dt_end])

    rotation = get_default_xtick_rotation(compress)
    plt.xticks(xticks, xticks_labels, rotation=rotation)

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
                    y_axhline2=[],
                    xlabel="", default_ylabel=False):
    """
    use ts1 as base ts (top plot). Only plot ts2[t] if t is present in ts1
    """

    plt.clf()
    matplotlib.rcParams.update({'font.size': 21})
    f, ax = plt.subplots(2, 1, figsize=(16, 12), sharex="col")

    if compress:
        x1, y1, x2, y2 = get_shared_compress(ts1.x, ts1.y, ts2.x, ts2.y)

        xticks = range(0, len(x1), 50)
        xticks_labels = copy.deepcopy(xticks)
    else:
        x1, y1 = ts1.x, ts1.y
        x2, y2 = ts2.x, ts2.y

        xticks, xticks_labels = get_xticks(ts1.dt_start, ts1.dt_end)

    plot_axvline(ts1, dt_axvline1, compress, ax[0])
    plot_axvline(ts1, dt_axvline2, compress, ax[1])

    for y in y_axhline2:
        ax[1].axhline(y, color="g", linewidth=2.0)

    if not title1:
        title1 = update_title(title1, ts1)
    if not title2:
        title2 = update_title(title2, ts2)

    if default_ylabel:
        ylabel1 = get_default_ylabel(ts1)
        ylabel2 = get_default_ylabel(ts2)

    ax[0].grid()
    ax[0].set_title(title1)
    ax[0].set_ylabel(ylabel1, fontsize=28)
    if ts1.metric == "loss":
        ax[0].set_yticks(get_default_yticks(ts1))
        ax[0].set_ylim([-0.02, 1.02])
    elif (ts1.metric == "throughput_down") or (ts1.metric == "throughput_up"):
        pass
        # ax[0].set_yscale('log')

    if ylim1 is not None:
        ax[0].set_ylim(ylim1)
    ax[0].set_xticks(xticks)
    if not compress:
        ax[0].set_xlim([ts1.dt_start, ts1.dt_end])
    if plot_type1 == "plot":
        ax[0].plot(x1, y1)
    else:
        ax[0].scatter(x1, y1, s=9)

    ax[1].grid()
    ax[1].set_title(title2)
    ax[1].set_ylabel(ylabel2, fontsize=28)
    if ts2.metric == "loss":
        ax[1].set_yticks(get_default_yticks(ts2))
        ax[1].set_ylim([-0.02, 1.02])
    elif (ts2.metric == "throughput_down") or (ts2.metric == "throughput_up"):
        pass
        # ax[1].set_yscale('log')

    if ylim2 is not None:
        ax[1].set_ylim(ylim2)
    if yticks2 is not None:
        ax[1].set_yticks(yticks2)
    if ytick_labels2 is not None:
        ax[1].set_yticklabels(ytick_labels2)
    ax[1].set_xlabel(xlabel, fontsize=28)
    ax[1].set_xticks(xticks)
    ax[1].set_xticklabels(xticks_labels, rotation=45)
    if not compress:
        ax[1].set_xlim([ts1.dt_start, ts1.dt_end])
    if plot_type2 == "plot":
        ax[1].plot(x2, y2)
    else:
        ax[1].scatter(x2, y2, s=9)

    plt.savefig(out_path)
    plt.close("all")


def plot_stl_decomposition(ts, ts_title, out_path):
    residual, seasonal, trend = ts.stl_decomposition()
    residual_trend = np.asarray(residual) + np.asarray(trend)
    x = range(len(ts.x))
    ylabel = get_default_ylabel(ts)
    xticks = range(0, len(x), 50)

    l = ts.y + residual + seasonal + trend
    ylim = [min(l) - 1, max(l) + 1]

    plt.clf()
    plt.figure(figsize=(24, 14))
    matplotlib.rcParams.update({'font.size': 21})
    gs = gridspec.GridSpec(6, 2)
    gs.update(wspace=0.3, hspace=0.4)

    ax_residual_trend = plt.subplot(gs[3:6, 0])
    ax_ts = plt.subplot(gs[0:3, 0], sharex=ax_residual_trend)
    ax_trend = plt.subplot(gs[4:6, 1])
    ax_seasonal = plt.subplot(gs[2:4, 1], sharex=ax_trend)
    ax_residual = plt.subplot(gs[0:2, 1], sharex=ax_trend)

    ax_ts.grid()
    ax_ts.set_ylim(ylim)
    ax_ts.set_ylabel(ylabel)
    ax_ts.set_title(ts_title)
    ax_ts.plot(x, ts.y)

    ax_residual_trend.grid()
    ax_residual_trend.set_ylim(ylim)
    ax_residual_trend.set_xlim([0, len(x)])
    ax_residual_trend.set_ylabel(ylabel)
    ax_residual_trend.set_xlabel("$i$")
    ax_residual_trend.set_title("residual + trend")
    ax_residual_trend.plot(x, residual_trend)
    ax_residual_trend.set_xticks(xticks)
    ax_residual_trend.set_xticklabels(map(str, xticks), rotation=45)

    ax_residual.grid()
    ax_residual.set_ylim(ylim)
    ax_residual.set_ylabel(ylabel)
    ax_residual.set_title("residual")
    ax_residual.plot(x, residual)

    ax_seasonal.grid()
    ax_seasonal.set_ylim(ylim)
    ax_seasonal.set_ylabel(ylabel)
    ax_seasonal.set_title("seasonal")
    ax_seasonal.plot(x, seasonal)

    ax_trend.grid()
    ax_trend.set_ylim(ylim)
    ax_trend.set_xlabel("$i$")
    ax_trend.set_ylabel(ylabel)
    ax_trend.set_title("trend")
    ax_trend.set_xticks(xticks)
    ax_trend.set_xticklabels(map(str, xticks), rotation=45)
    ax_trend.plot(x, trend)

    plt.setp(ax_ts.get_xticklabels(), visible=False)
    plt.setp(ax_residual.get_xticklabels(), visible=False)
    plt.setp(ax_seasonal.get_xticklabels(), visible=False)

    plt.savefig(out_path)
    plt.close("all")
