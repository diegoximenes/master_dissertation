import os
import sys
from datetime import datetime
import numpy as np
import matplotlib
import matplotlib.pylab as plt

sys.path.append("../../utils")
from time_series import TimeSeries
import plot_procedures

dt_start = datetime(2016, 5, 1)
dt_end = datetime(2016, 5, 20)
# targets = "all"
targets = [["BHZRENPEV01", "64:66:B3:A6:BA:54"],
           ["BREDTCSRV20", "64:66:B3:7B:9E:6A"],
           ["NHODTCSRV04", "64:66:B3:50:05:BC"],
           ["CPSDTCSRV02", "64:66:B3:7B:9D:C4"],
           ["NHODTCSRV04", "64:66:B3:50:06:90"]]


def acf(in_path, server, mac):
    ts = TimeSeries(in_path, "loss", dt_start=dt_start, dt_end=dt_end,
                    ts_type="hourly")
    lags, acf, cnt_pairs = ts.get_acf(84)

    print "cnt_pairs={}".format(cnt_pairs)
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.grid()
    plt.ylim([-0.3, 1.0])
    plt.yticks(np.arange(-0.3, 1.1, 0.1))
    plt.xticks(range(0, 85, 12), rotation=45)
    plt.xlabel("Lag (hours)")
    plt.ylabel("ACF")
    plt.plot(lags, acf, marker="o")
    plt.savefig("./plots/acf/acf_{}_{}.png".format(server, mac))


def mean_per_hour(in_path, server, mac):
    ts = TimeSeries(in_path, "loss", dt_start=dt_start, dt_end=dt_end,
                    ts_type="hourly")
    ts.compress()
    plot_procedures.plot_ts(ts, "./plots/ts/ts_{}_{}.png".format(server, mac),
                            ylim=[-0.05, 1.05], ylabel="Loss Fraction",
                            xlabel="day/month")


def mean_per_hour_in_a_day(in_path, server, mac):
    ts = TimeSeries(in_path, "loss", dt_start=dt_start, dt_end=dt_end)
    hour_samples, hour_cnt = [], []
    for hour in xrange(24):
        hour_samples.append([])
        hour_cnt.append(0)
    for i in xrange(len(ts.x)):
        hour_samples[ts.x[i].hour].append(ts.y[i])
        hour_cnt[ts.x[i].hour] += 1

    hour_list, mean_list, var_list = [], [], []
    for hour in xrange(24):
        if len(hour_samples) > 0:
            hour_list.append(hour)
            mean_list.append(np.mean(hour_samples[hour]))
            var_list.append(np.var(hour_samples[hour]))
    hour_list = np.asarray(hour_list)
    mean_list = np.asarray(mean_list)
    var_list = np.asarray(var_list)

    print "hour_cnt={}".format(hour_cnt)
    plt.clf()
    matplotlib.rcParams.update({'font.size': 30})
    plt.gcf().set_size_inches(16, 15)
    plt.grid()
    plt.ylabel("Mean Loss Fraction")
    plt.xlabel("Hour")
    plt.xticks(range(0, 24, 2), rotation=45)
    plt.plot(hour_list, mean_list, marker="o")
    plt.fill_between(hour_list, mean_list - var_list, mean_list + var_list,
                     alpha=0.3)
    plt.savefig("./plots/mean_per_hour_in_a_day/mean_per_hour_in_a_day_{}_{}."
                "png".format(server, mac))


def write_all_samples_to_file(targets, in_dir):
    samples = []
    for target in targets:
        server, mac = target[0], target[1]
        in_path = "{}/{}/{}.csv".format(in_dir, server, mac)
        ts = TimeSeries(in_path, "loss", dt_start=dt_start, dt_end=dt_end)
        samples = samples + ts.y
        print "server={}, mac={}".format(server, mac)

    with open("./plots/distribution/samples.csv", "w") as f:
        f.write("loss\n")
        for x in samples:
            f.write("{}\n".format(x))


def loss_descriptive_analysis():
    in_dir = "../../input/{}_{}/".format(dt_start.year,
                                         str(dt_start.month).zfill(2))

    global targets
    if targets == "all":
        targets = []
        for server in os.listdir(in_dir):
            for file_name in os.listdir("{}/{}".format(in_dir, server)):
                mac = file_name.split(".")[0]
                targets.append([server, mac])

    for target in targets:
        server, mac = target[0], target[1]
        in_path = "{}/{}/{}.csv".format(in_dir, server, mac)
        print "server={}, mac={}".format(server, mac)

        acf(in_path, server, mac)
        mean_per_hour(in_path, server, mac)
        mean_per_hour_in_a_day(in_path, server, mac)

    # write_all_samples_to_file(targets, in_dir)


if __name__ == "__main__":
    loss_descriptive_analysis()
