import os
import sys
import ast
import copy
import datetime
import functools
import pandas as pd
from itertools import izip

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.read_input as read_input
import utils.utils as utils
from utils.time_series import TimeSeries


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
                                     (not utils.is_valid_ip(name)))):
                ip_name[ip] = name
    return ip_name


def get_name(name, ip_name):
    if not utils.is_valid_ip(name):
        return name
    else:
        # name is an ip
        return ip_name.get(name)


def get_traceroute(ts_traceroute, ts_server_ip, allow_embratel,
                   compress_embratel):
    hops_default_names = []
    hops_default_ips = []
    server_ip = None
    for i in xrange(len(ts_traceroute.y)):
        traceroute = copy.deepcopy(ts_traceroute.y[i])
        server_ip = ts_server_ip.y[i]

        if allow_embratel and compress_embratel:
            # rename embratel equipments to "embratel"
            for hop in traceroute:
                for j in range(len(hop["names"])):
                    if "embratel" in hop["names"][j]:
                        hop["names"][j] = "embratel"
                        hop["ips"][j] = "embratel"

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
                if not allow_embratel:
                    for name, ip in izip(hop["names"], hop["ips"]):
                        if "embratel" in name:
                            return (False, "hop_with_embratel={}".format(hop),
                                    server_ip)
                for name, ip in izip(hop["names"], hop["ips"]):
                    if (name != u"##"):
                        hop_name = get_name(name, ip_name)
                        hop_ip = ip
                for name, ip in izip(hop["names"], hop["ips"]):
                    if name == u"##":
                        hop_name = hop_ip = None
                        break

                # check if more than one name appear in the
                # same hop
                if hop_name is not None:
                    for name in hop["names"]:
                        if ((name != u"##") and
                                (hop_name != get_name(name, ip_name))):
                            return (False, "diff_name_same_hop={}".format(hop),
                                    server_ip)

                hops_names.append(hop_name)
                hops_ips.append(hop_ip)

            if allow_embratel and compress_embratel and hops_names:
                # compress embratel hops
                hops_names_aux = [hops_names[0]]
                hops_ips_aux = [hops_ips[0]]
                for j in xrange(1, len(hops_names)):
                    if ((hops_names[j] == "embratel") and
                            (hops_names_aux[-1] == "embratel")):
                        continue
                    hops_names_aux.append(hops_names[j])
                    hops_ips_aux.append(hops_ips[j])
                hops_names = hops_names_aux
                hops_ips = hops_ips_aux

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

    for name in hops_default_names:
        if name and (hops_default_names.count(name) > 1):
            return (False,
                    "more_than_one_occurrence={}".format(hops_default_names),
                    server_ip)

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
                    if not utils.is_private_ip(traceroute[j][1]):
                        filtered = (traceroute[i], traceroute[j])
                        break
            if filtered == ((None, None), (None, None)):
                filtered = (traceroute[i], traceroute[i])

        traceroute_filtered.append(filtered)
    return traceroute_filtered


def compress_traceroute(traceroute, traceroute_type):
    """
    remove left/right ((None, None), (None, None)) hops from
    traceroute_filtered or (None, None) from traceroute
    """

    if traceroute_type == "filtered":
        target_hop = ((None, None), (None, None))
    elif traceroute_type == "raw":
        target_hop = (None, None)

    i = 0
    j = len(traceroute) - 1
    while (i < len(traceroute)) and (traceroute[i] == target_hop):
        i += 1
    while (j >= 0) and (traceroute[j] == target_hop):
        j -= 1

    if j >= i:
        compressed = copy.deepcopy(traceroute[i:j + 1])
    else:
        compressed = []
    return compressed


def print_traceroute_per_mac(dt_start, dt_end, mac_node, allow_embratel):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/not_filtered/traceroute_per_mac.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        f.write("server,server_ip,node,mac,is_unique_traceroute,traceroute,"
                "is_unique_traceroute_not_compress_embratel,"
                "traceroute_not_compress_embratel\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts_traceroute = TimeSeries(in_path=in_path, metric="traceroute",
                                       dt_start=dt_start, dt_end=dt_end)
            ts_server_ip = TimeSeries(in_path=in_path, metric="server_ip",
                                      dt_start=dt_start, dt_end=dt_end)

            is_unique_traceroute, str_traceroute, server_ip = \
                get_traceroute(ts_traceroute, ts_server_ip, allow_embratel,
                               True)
            if allow_embratel:
                (is_unique_traceroute_not_compress_embratel,
                 str_traceroute_not_compress_embratel, _) = \
                    get_traceroute(ts_traceroute, ts_server_ip, allow_embratel,
                                   False)
            else:
                (is_unique_traceroute_not_compress_embratel,
                 str_traceroute_not_compress_embratel) = (None, None)

            node = mac_node.get(mac)

            l_formatter = "{},{},{},{},{},\"{}\",{},\"{}\"\n"
            l = l_formatter.format(server, server_ip, node, mac,
                                   is_unique_traceroute, str_traceroute,
                                   is_unique_traceroute_not_compress_embratel,
                                   str_traceroute_not_compress_embratel)
            f.write(l)
    utils.sort_csv_file(out_path, ["server", "node"])


def print_traceroute_per_mac_filtered(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/filtered/traceroute_per_mac.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        f.write("server,node,mac,traceroute_filtered,is_unique_traceroute,"
                "traceroute\n")
        in_path = ("{}/prints/{}/not_filtered/traceroute_per_mac.csv".
                   format(script_dir, str_dt))
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            if row["is_unique_traceroute"] is False:
                continue

            traceroute_filtered = compress_traceroute(
                get_traceroute_filtered(row["traceroute"]), "filtered")
            traceroute = ast.literal_eval(row["traceroute"])
            traceroute = compress_traceroute(traceroute, "raw")

            if traceroute_filtered == []:
                continue
            target_traceroute = True
            for hop in traceroute_filtered:
                if hop[0][0] is None:
                    target_traceroute = False
                    break
                if (utils.is_private_ip(hop[0][1]) and
                        utils.is_private_ip(hop[1][1])):
                    target_traceroute = False
                    break
            if not target_traceroute:
                continue

            aux_traceroute_filtered = copy.deepcopy(traceroute_filtered)
            traceroute_filtered = []
            for hop in aux_traceroute_filtered:
                if ((hop[0][0] is not None) and
                        (hop[0][1].split(".")[0] == "192")):
                    continue
                traceroute_filtered.append(hop)

            l = ("{},{},{},\"{}\",{},\"{}\"\n".
                 format(row["server"], row["node"], row["mac"],
                        traceroute_filtered, row["is_unique_traceroute"],
                        traceroute))
            f.write(l)
    utils.sort_csv_file(out_path, ["traceroute_filtered", "server", "mac"])


def print_macs_per_name_filtered(dt_start, dt_end, mac_node):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    in_path = ("{}/prints/{}/filtered/traceroute_per_mac.csv".
               format(script_dir, str_dt))
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

    out_path = ("{}/prints/{}/filtered/macs_per_name.csv".
                format(script_dir, str_dt))
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

    out_path = "{}/prints/{}/not_filtered/name_ips.csv".format(script_dir,
                                                               str_dt)
    with open(out_path, "w") as f:
        f.write("name,ips\n")
        for name in sorted(name_ip.keys()):
            f.write("{},{}\n".format(name, sorted(list(name_ip[name]))))


def print_names_per_mac(dt_start, dt_end, mac_node):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/not_filtered/names_per_mac.csv".
                format(script_dir, str_dt))
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

    out_path = ("{}/prints/{}/not_filtered/macs_per_name.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        f.write("name,macs\n")
        names = sorted(name_macs.keys())
        for name in names:
            f.write("{},\"{}\"\n".format(name, sorted(list(name_macs[name]))))


def print_all(dt_start, dt_end, mac_node):
    str_dt = utils.get_str_dt(dt_start, dt_end)
    utils.create_dirs(["{}/prints".format(script_dir),
                       "{}/prints/{}".format(script_dir, str_dt),
                       "{}/prints/{}/filtered".format(script_dir, str_dt),
                       "{}/prints/{}/not_filtered".format(script_dir, str_dt)])

    # print_macs_per_name(dt_start, dt_end, mac_node)
    # print_names_per_mac(dt_start, dt_end, mac_node)
    # print_name_ips(dt_start, dt_end)
    print_traceroute_per_mac(dt_start, dt_end, mac_node, True)

    print_traceroute_per_mac_filtered(dt_start, dt_end)
    # print_macs_per_name_filtered(dt_start, dt_end, mac_node)


def run_sequential(mac_node):
    for dt_start, dt_end in utils.iter_dt_range():
        print_all(dt_start, dt_end, mac_node)


def run_parallel(mac_node):
    dt_ranges = list(utils.iter_dt_range())
    f_print_all = functools.partial(print_all, mac_node=mac_node)
    utils.parallel_exec(f_print_all, dt_ranges)


def run_single(mac_node, dt_start, dt_end):
    print_all(dt_start, dt_end, mac_node)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    mac_node = read_input.get_mac_node()

    # run_single(mac_node, dt_start, dt_end)
    run_parallel(mac_node)
    # run_sequential(mac_node)
