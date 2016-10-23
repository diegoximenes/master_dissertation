import os
import sys
import datetime

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)


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
                print "cnt={}, server={}, mac={}".format(cnt, server, mac)

            yield server, mac, in_path


def create_dirs(dirs):
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
