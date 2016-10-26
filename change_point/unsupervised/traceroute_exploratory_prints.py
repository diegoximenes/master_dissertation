import os
import sys
import ast
import copy
import socket
import datetime
from IPy import IP
import pandas as pd
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.read_input as read_input
import utils.utils as utils
from utils.time_series import TimeSeries


def is_valid_ip(str_ip):
    try:
        socket.inet_aton(str_ip)
        return True
    except socket.error:
        return False


def is_private_ip(str_ip):
    if not is_valid_ip(str_ip):
        return False
    ip = IP(str_ip)
    return (ip.iptype() == "PRIVATE")


def get_ip_name(traceroute):
    """
    get the ip->name mapping:
    the dns resolution can fail, and the ip can be
    displayed at the "names" field
    """

    ip_name = {}
    for hop in traceroute:
        for ip, name in izip(hop["ips"], hop["names"]):
            if ((name != u"##") and ((ip not in ip_name) or
                                     (not is_valid_ip(name)))):
                ip_name[ip] = name
    return ip_name


def get_name(name, ip_name):
    if not is_valid_ip(name):
        return name
    else:
        # name is an ip
        return ip_name.get(name)


def get_traceroute(ts_traceroute, ts_server_ip):
    hops_default_names = []
    hops_default_ips = []
    for traceroute, server_ip in izip(ts_traceroute.y, ts_server_ip):
        # THIS PIECE OF CODE EXPOSES A TRACEROUTE INCONSISTENCY
        # IN 2016_06
        # if traceroute:
        #     cnt = 0
        #     for hop in traceroute:
        #         if ((hop["names"] is not None) and
        #                 (u"10.12.0.1" in hop["names"])):
        #             cnt += 1
        #     if cnt > 1:
        #         for hop in traceroute:
        #             print "hop={}".format(hop)
        #         print ("mac={}, server={}, row.dt={}".
        #                format(mac, server, row["dt"]))
        #
        #         return

        if traceroute:
            ip_name = get_ip_name(traceroute)

            hops_names = []
            hops_ips = []
            for hop in traceroute:
                # get a single name for each hop
                hop_name = hop_ip = None
                for name, ip in izip(hop["names"], hop["ips"]):
                    if (name != u"##"):
                        hop_name = get_name(name, ip_name)
                        hop_ip = ip

                # check if more than one name appear in the
                # same hop
                for name in hop["names"]:
                    if ((name != u"##") and
                            (hop_name != get_name(name, ip_name))):
                        return (False, "diff_name_same_hop={}".format(hop),
                                server_ip)

                hops_names.append(hop_name)
                hops_ips.append(hop_ip)

            if not hops_default_names:
                hops_default_names = copy.deepcopy(hops_names)
                hops_default_ips = copy.deepcopy(hops_ips)
            else:
                update_hops_default = False
                for name_hops, name_hops_default in izip(hops_names,
                                                         hops_default_names):
                    if ((name_hops is not None) and
                            (name_hops_default is None)):
                        # current traceroute have more
                        # information than previous ones
                        update_hops_default = True
                    elif ((name_hops is not None) and
                          (name_hops_default is not None) and
                          (name_hops != name_hops_default)):
                        # different traceroutes
                        return (False,
                                "hops1={},hops2={}".format(hops_names,
                                                           hops_default_names),
                                server_ip)

                if update_hops_default:
                    hops_default_names = copy.deepcopy(hops_names)
                    hops_default_ips = copy.deepcopy(hops_ips)

    hops_default = []
    for name_hops_default, ip_hops_default in izip(hops_default_names,
                                                   hops_default_ips):
        hops_default.append((name_hops_default, ip_hops_default))
    return True, "{}".format(hops_default), server_ip


def get_traceroute_filtered(str_traceroute_list):
    """
    if the ip is private get the next ip in traceroute that is public
    """

    traceroute = ast.literal_eval(str_traceroute_list)

    traceroute_filtered = []
    for i in xrange(len(traceroute) - 1):
        filtered = ((None, None), (None, None))
        if traceroute[i] != (None, None):
            for j in xrange(i, len(traceroute)):
                if traceroute[j] != (None, None):
                    if not is_private_ip(traceroute[j][1]):
                        filtered = (traceroute[i], traceroute[j])
                        break
            if filtered == ((None, None), (None, None)):
                filtered = (traceroute[i], traceroute[i])

        traceroute_filtered.append(filtered)
    return traceroute_filtered


def compress_traceroute(traceroute, traceroute_type):
    """
    remove lasts ((None, None), (None, None)) hops from traceroute_filtered or
    (None, None) from traceroute
    """

    if traceroute_type == "filtered":
        target_hop = ((None, None), (None, None))
    elif traceroute_type == "raw":
        target_hop = (None, None)

    compressed = []
    for hop in reversed(traceroute):
        if (not compressed) and (hop == target_hop):
            continue
        compressed.append(hop)
    compressed.reverse()
    return compressed


def print_traceroute_per_mac(dt_start, dt_end, mac_node):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = "{}/prints/{}/traceroute_per_mac.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("server,server_ip,node,mac,is_unique_traceroute,traceroute\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts_traceroute = TimeSeries(in_path=in_path, metric="traceroute",
                                       dt_start=dt_start, dt_end=dt_end)
            ts_server_ip = TimeSeries(in_path=in_path, metric="server_ip",
                                      dt_start=dt_start, dt_end=dt_end)

            is_unique_traceroute, str_traceroute, server_ip = \
                get_traceroute(ts_traceroute, ts_server_ip)
            node = mac_node.get(mac)
            f.write("{},{},{},{},{},\"{}\"\n".format(server, server_ip, node,
                                                     mac, is_unique_traceroute,
                                                     str_traceroute))
    utils.sort_csv_file(out_path, ["server", "node"])


def print_traceroute_per_mac_filtered(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/traceroute_per_mac_filtered.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        f.write("server,node,mac,is_unique_traceroute,traceroute,"
                "traceroute_filtered\n")
        in_path = "{}/prints/{}/traceroute_per_mac.csv".format(script_dir,
                                                               str_dt)
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            if row["is_unique_traceroute"] is False:
                continue

            traceroute_filtered = compress_traceroute(
                get_traceroute_filtered(row["traceroute"]), "filtered")
            traceroute = ast.literal_eval(row["traceroute"])
            traceroute = compress_traceroute(traceroute, "raw")

            l = ("{},{},{},{},\"{}\",\"{}\"\n".
                 format(row["server"], row["node"], row["mac"],
                        row["is_unique_traceroute"], traceroute,
                        traceroute_filtered))
            f.write(l)


def print_macs_per_name_filtered(dt_start, dt_end, mac_node):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = "{}/prints/{}/traceroute_per_mac_filtered.csv".format(script_dir,
                                                                    str_dt)
    name_macs = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        traceroute_filtered = ast.literal_eval(row["traceroute_filtered"])
        for elem in traceroute_filtered:
            name0 = elem[0][0]
            name1 = elem[1][0]
            tp = (name0, name1)
            if tp not in name_macs:
                name_macs[tp] = set()
            name_macs[tp].add((row["server"],
                               mac_node.get(row["mac"]),
                               row["mac"]))

    out_path = "{}/prints/{}/macs_per_name_filtered.csv".format(script_dir,
                                                                str_dt)
    with open(out_path, "w") as f:
        f.write("name,macs\n")
        names = sorted(name_macs.keys())
        for name in names:
            f.write("\"{}\",\"{}\"\n".format(name,
                                             sorted(list(name_macs[name]))))


def print_name_ips(dt_start, dt_end):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    name_ip = {}
    for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
        ts = TimeSeries(in_path=in_path, metric="traceroute",
                        dt_start=dt_start, dt_end=dt_end)
        for traceroute in ts.y:
            if traceroute:
                for hop in traceroute:
                    for name, ip in izip(hop["names"], hop["ips"]):
                        if name not in name_ip:
                            name_ip[name] = set()
                        name_ip[name].add(ip)

    out_path = "{}/prints/{}/name_ips.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("name,ips\n")
        for name in sorted(name_ip.keys()):
            f.write("{},{}\n".format(name, sorted(list(name_ip[name]))))


def print_names_per_mac(dt_start, dt_end, mac_node):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = "{}/prints/{}/names_per_mac.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("server,node,mac,names\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts = TimeSeries(in_path=in_path, metric="traceroute",
                            dt_start=dt_start, dt_end=dt_end)
            names = set()
            for traceroute in ts.y:
                if traceroute:
                    ip_name = get_ip_name(traceroute)
                    for hop in traceroute:
                        for name in hop["names"]:
                            names.add(get_name(name, ip_name))
            node = mac_node.get(mac)
            f.write("{},{},{},\"{}\"\n".format(server, node, mac,
                                               sorted(list(names))))

    utils.sort_csv_file(out_path, ["server", "node"])


def print_macs_per_name(dt_start, dt_end, mac_node):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    name_macs = {}
    for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
        ts = TimeSeries(in_path=in_path, metric="traceroute",
                        dt_start=dt_start, dt_end=dt_end)
        for traceroute in ts.y:
            if traceroute:
                ip_name = get_ip_name(traceroute)
                for hop in traceroute:
                    for name in hop["names"]:
                        name = get_name(name, ip_name)
                        if name not in name_macs:
                            name_macs[name] = set()
                        name_macs[name].add((server, mac_node.get(mac), mac))

    out_path = "{}/prints/{}/macs_per_name.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("name,macs\n")
        names = sorted(name_macs.keys())
        for name in names:
            f.write("{},\"{}\"\n".format(name, sorted(list(name_macs[name]))))


if __name__ == "__main__":
    mac_node = read_input.get_mac_node()

    for month in xrange(7, 10):
        for day_start in (1, 11, 21):
            dt_start = datetime.datetime(2016, month, day_start)
            dt_end = dt_start + datetime.timedelta(days=10)

            str_dt = utils.get_str_dt(dt_start, dt_end)
            utils.create_dirs(["{}/prints".format(script_dir),
                               "{}/prints/{}".format(script_dir, str_dt)])

            print_macs_per_name(dt_start, dt_end, mac_node)
            print_names_per_mac(dt_start, dt_end, mac_node)
            print_name_ips(dt_start, dt_end)
            print_traceroute_per_mac(dt_start, dt_end, mac_node)

            print_traceroute_per_mac_filtered(dt_start, dt_end)
            print_macs_per_name_filtered(dt_start, dt_end, mac_node)
            break
        break
