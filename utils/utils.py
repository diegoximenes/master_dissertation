import os
import sys
import socket
import signal
import datetime
import pandas as pd
import numpy as np
from IPy import IP
from multiprocessing import Pool
from functools import partial

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)


def get_client(server, mac):
    return (server, mac)


def f_unpack(args, f):
    return f(*args)


def parallel_exec(f, args_l, n_processes=4):
    # check python bug: http://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    f_parallel = partial(f_unpack, f=f)

    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(processes=n_processes)
    signal.signal(signal.SIGINT, original_sigint_handler)

    try:
        pool.map_async(f_parallel, args_l).get(np.inf)
    except KeyboardInterrupt:
        pool.terminate()
    else:
        pool.close()
    pool.join()


def get_str_dt(dt_start, dt_end):
    return "dtstart{}_dtend{}".format(dt_start.strftime("%Y-%m-%d"),
                                      dt_end.strftime("%Y-%m-%d"))


def get_dt_dir(dt_start, dt_end):
    """
    considers that [dt_start, dt_end) is inside the same month
    """

    d1 = datetime.datetime(dt_start.year, dt_start.month, 1)
    if dt_start.month == 12:
        d2 = datetime.datetime(dt_start.year + 1, 1, 1)
    else:
        d2 = datetime.datetime(dt_start.year, dt_start.month + 1, 1)
    return get_str_dt(d1, d2)


def get_out_file_name(server, mac, dt_start, dt_end):
    return "server{}_mac{}_{}".format(server, mac,
                                      get_str_dt(dt_start, dt_end))


def get_in_path(server, mac, dt_start, dt_end):
    return "{}/input/{}/{}/{}.csv".format(base_dir,
                                          get_dt_dir(dt_start, dt_end),
                                          server,
                                          mac)


def iter_dt_range():
    year = 2016
    months = range(5, 11)
    day_starts = (1, 11, 21)
    delta_days = 10

    for month in months:
        for day_start in day_starts:
            dt_start = datetime.datetime(year, month, day_start)
            dt_end = dt_start + datetime.timedelta(days=delta_days)
            yield dt_start, dt_end


def iter_server_mac(dt_dir, print_iter=False):
    cnt = 0
    for server in os.listdir("{}/input/{}".format(base_dir, dt_dir)):
        for file_name in os.listdir("{}/input/{}/{}".format(base_dir, dt_dir,
                                                            server)):
            mac = file_name.split(".csv")[0]
            in_path = "{}/input/{}/{}/{}".format(base_dir, dt_dir, server,
                                                 file_name)

            if print_iter:
                cnt += 1
                print "cnt={}, server={}, mac={}, dt_dir={}".format(cnt,
                                                                    server,
                                                                    mac,
                                                                    dt_dir)

            yield server, mac, in_path


def create_dirs(dirs):
    for dir in dirs:
        try:
            os.makedirs(dir)
        except OSError:
            pass


def sort_csv_file(path, fields, ascending=None):
    if ascending is None:
        ascending = [True] * len(fields)
    df = pd.read_csv(path)
    df_sorted = df.sort_values(by=fields, ascending=ascending)
    df_sorted.to_csv(path, index=False)


def is_valid_ip(str_ip):
    try:
        socket.inet_aton(str_ip)
        return True
    except (socket.error, UnicodeEncodeError):
        return False


def is_private_ip(str_ip):
    if not is_valid_ip(str_ip):
        return False
    ip = IP(str_ip)
    return (ip.iptype() == "PRIVATE")
