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
import change_point.cp_utils.cp_utils as cp_utils


def get_ip_name(traceroutes):
    """
    get the ip->name mapping:
    the dns resolution can fail, and the ip can be
    displayed at the "names" field
    """

    ip_name = {}
    for traceroute in traceroutes:
        for hop in traceroute:
            for ip, name in izip(hop["ips"], hop["names"]):
                if name != u"##":
                    if ip not in ip_name:
                        ip_name[ip] = name
                    elif utils.is_valid_ip(ip_name[ip]):
                        ip_name[ip] = name
                    elif ((not utils.is_valid_ip(ip_name[ip])) and
                          (not utils.is_valid_ip(name)) and
                          (ip_name[ip] != name)):
                        return {}
    return ip_name


def get_name(name, ip_name):
    if not utils.is_valid_ip(name):
        return name
    else:
        # name is an ip
        return ip_name.get(name)


def get_traceroute(ts_traceroute, allow_embratel, compress_embratel,
                   allow_last_hop_embratel):
    hops_default = []

    # sometimes only a few traceroutes present different names in the same hop
    cnt_diff_name_same_hop = 0
    thresh_diff_name_same_hop = 0.01

    ip_name = get_ip_name(ts_traceroute.y)
    # considering dynamic ips, is possible that during a time interval,
    # the same ip is used for more than one equipments
    update_ip_name = False
    if not ip_name:
        update_ip_name = True

    for i in xrange(len(ts_traceroute.y)):
        traceroute = copy.deepcopy(ts_traceroute.y[i])

        # some traceroutes presents a weak inconsistency then ignore them
        ignore_traceroute = False

        if traceroute:
            if update_ip_name:
                ip_name = get_ip_name([traceroute])

            # rename embratel equipments to "embratel"
            if allow_embratel and compress_embratel:
                for hop in traceroute:
                    for j in xrange(len(hop["names"])):
                        if "embratel" in get_name(hop["names"][j], ip_name):
                            hop["names"][j] = "embratel"
                            hop["ips"][j] = "embratel"

            # get a single (hop name, hop ip) tuple for each hop of the current
            # traceroute. If there are strong inconsistencies return False
            hops_current = []
            for hop in traceroute:
                # check if there is an unwanted embratel hop
                if not allow_embratel:
                    for name in hop["names"]:
                        if "embratel" in name:
                            return (False, "hop_with_embratel={}".format(hop))

                # get a single name for each hop
                hop_name = hop_ip = None
                for name, ip in izip(hop["names"], hop["ips"]):
                    if (name != u"##"):
                        hop_name = get_name(name, ip_name)
                        hop_ip = ip

                # check if more than one name appear in the same hop
                if hop_name is not None:
                    for name in hop["names"]:
                        if name == u"##":
                            ignore_traceroute = True

                        if ((name != u"##") and
                                (hop_name != get_name(name, ip_name))):
                            cnt_diff_name_same_hop += 1
                            frac_diff_name_same_hop = \
                                (float(cnt_diff_name_same_hop) /
                                 len(ts_traceroute.y))
                            if (frac_diff_name_same_hop >
                                    thresh_diff_name_same_hop):
                                return (False,
                                        "cnt_diff_name_same_hop={},"
                                        "diff_name_same_hop={}".
                                        format(cnt_diff_name_same_hop, hop))
                            else:
                                ignore_traceroute = True
                                continue

                hops_current.append({"name": hop_name, "ip": hop_ip})

            if ignore_traceroute:
                continue

            # compress embratel hops
            if allow_embratel and compress_embratel and hops_current:
                hops_current_aux = [hops_current[0]]
                for j in xrange(1, len(hops_current)):
                    if ((hops_current[j]["name"] == "embratel") and
                            (hops_current_aux[-1]["name"] == "embratel")):
                        continue
                    hops_current_aux.append(hops_current[j])
                hops_current = hops_current_aux

            if not hops_default:
                # first traceroute to be analysed
                hops_default = hops_current
            else:
                # check if current traceroute has more info than previous ones.
                # Also checks if current traceroute is different from previous
                # ones.

                update_hops_default = False

                for j in xrange(min(len(hops_current), len(hops_default))):
                    name_current = hops_current[j]["name"]
                    ip_current = hops_current[j]["ip"]
                    name_default = hops_default[j]["name"]
                    ip_default = hops_default[j]["ip"]

                    if ((name_current is not None) and
                            (name_default is None)):
                        # current traceroute have more info than previous ones
                        update_hops_default = True
                    elif ((name_current is not None) and
                          (name_default is not None) and
                          (name_current != name_default)):
                        if ((ip_default is not None) and
                                (ip_current is not None) and
                                (ip_current == ip_default)):
                            # since dns can fail and the ip can be places at
                            # the names field, the same hop can have different
                            # names. Therefore if names are different also
                            # check if ips are differents
                                if not utils.is_valid_ip(name_current):
                                    update_hops_default = True
                        else:
                            # different traceroutes
                            return (False,
                                    "hops1={},hops2={},traceroute1={},"
                                    "traceroute2={}".format(hops_current[j],
                                                            hops_default[j],
                                                            hops_current,
                                                            hops_default))

                # current traceroute has more info than prevous ones
                if len(hops_current) > len(hops_default):
                    update_hops_default = True

                if update_hops_default:
                    hops_default = hops_current

    # check if the same name appears in more than one hop
    name_set = set()
    for hop in hops_default:
        name = hop["name"]
        if (name is not None) and (name in name_set):
            return (False, "more_than_one_occurrence={}".format(hops_default))
        else:
            name_set.add(name)

    # check if last hop is embratel
    if not allow_last_hop_embratel:
        for hop in reversed(hops_default):
            if hop["name"] == "embratel":
                return False, "last_hop_with_embratel={}".format(hops_default)
            elif hop["name"] is not None:
                break

    # check if reached server in less hops than the maximum allowed
    if hops_default and (hops_default[-1]["name"] is not None):
        return False, "last_hop_diff_than_none={}".format(hops_default)

    # compress traceroute: remove nones from left and right
    i = 0
    j = len(hops_default) - 1
    while (i < len(hops_default)) and (hops_default[i]["name"] is None):
        i += 1
    while (j >= 0) and (hops_default[j]["name"] is None):
        j -= 1
    if j >= i:
        hops_default = hops_default[i:j + 1]
    else:
        return False, "empty_traceroute"

    # check if there are Nones after compression
    for hop in hops_default:
        if hop["name"] is None:
            return False, "traceroute_with_nones={}".format(hops_default)

    # check if there is at least one public ip
    has_public_ip = False
    for hop in hops_default:
        if not utils.is_private_ip(hop["ip"]):
            has_public_ip = True
            break
    if not has_public_ip:
        return False, "no_public_ip={}".format(hops_default)

    # convert to format to be consumed by other procedures
    ret_hops_default = []
    for hop in hops_default:
        ret_hops_default.append((hop["name"], hop["ip"]))
    return True, ret_hops_default


def get_traceroute_filtered(valid_traceroute, str_traceroute, server):
    """
    if the ip is private get the next ip in traceroute that is public
    """

    if not valid_traceroute:
        return "not_valid"

    traceroute = ast.literal_eval(str_traceroute)

    # remove local ip
    if traceroute[0][0].split(".")[0] == "192":
        traceroute = traceroute[1:]

    # to each hop, add next hop with public ip
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
    if traceroute:
        traceroute_filtered.append((traceroute[-1], traceroute[-1]))

    # add server hop
    traceroute_filtered += ((server, server), (server, server))

    return traceroute_filtered


def print_traceroute_per_mac(dt_start, dt_end):
    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/not_filtered/traceroute_per_mac.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        f.write("server,mac,"
                "valid_traceroute_compress_embratel,"
                "traceroute_compress_embratel,"
                "valid_traceroute_compress_embratel_without_last_hop_embratel,"
                "traceroute_compress_embratel_without_last_hop_embratel,"
                "valid_traceroute_without_embratel,"
                "traceroute_without_embratel,"
                "valid_traceroute,"
                "traceroute\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts_traceroute = TimeSeries(in_path=in_path, metric="traceroute",
                                       dt_start=dt_start, dt_end=dt_end)

            (valid_traceroute_compress_embratel,
             traceroute_compress_embratel) = \
                get_traceroute(ts_traceroute, True, True, True)

            (valid_traceroute_compress_embratel_without_last_hop_embratel,
             traceroute_compress_embratel_without_last_hop_embratel) = \
                get_traceroute(ts_traceroute, True, True, False)

            (valid_traceroute_without_embratel,
             traceroute_without_embratel) = \
                get_traceroute(ts_traceroute, False, False, False)

            (valid_traceroute, traceroute) = \
                get_traceroute(ts_traceroute, True, False, False)

            l = "{},{}" + ",{},\"{}\"" * 4 + "\n"
            l = l.format(
                server, mac,
                valid_traceroute_compress_embratel,
                traceroute_compress_embratel,
                valid_traceroute_compress_embratel_without_last_hop_embratel,
                traceroute_compress_embratel_without_last_hop_embratel,
                valid_traceroute_without_embratel,
                traceroute_without_embratel,
                valid_traceroute,
                traceroute)
            f.write(l)
    utils.sort_csv_file(out_path, ["server", "mac"])


def print_traceroute_per_mac_filtered(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = ("{}/prints/{}/filtered/traceroute_per_mac.csv".
                format(script_dir, str_dt))
    with open(out_path, "w") as f:
        l = ("server,mac,"
             "valid_traceroute_compress_embratel,"
             "traceroute_compress_embratel_filter,"
             "valid_traceroute_compress_embratel_without_last_hop_embratel,"
             "traceroute_compress_embratel_without_last_hop_embratel_filter,"
             "valid_traceroute_without_embratel,"
             "traceroute_without_embratel_filter,"
             "valid_traceroute,"
             "traceroute_filter\n")
        f.write(l)

        in_path = ("{}/prints/{}/not_filtered/traceroute_per_mac.csv".
                   format(script_dir, str_dt))
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            traceroute_compress_embratel_filter = \
                get_traceroute_filtered(
                    row["valid_traceroute_compress_embratel"],
                    row["traceroute_compress_embratel"],
                    row["server"])

            traceroute_compress_embratel_without_last_hop_embratel_filter = \
                get_traceroute_filtered(
                    row["valid_traceroute_compress_embratel_"
                        "without_last_hop_embratel"],
                    row["traceroute_compress_embratel_"
                        "without_last_hop_embratel"],
                    row["server"])

            traceroute_without_embratel_filter = \
                get_traceroute_filtered(
                    row["valid_traceroute_without_embratel"],
                    row["traceroute_without_embratel"],
                    row["server"])

            traceroute_filter = \
                get_traceroute_filtered(
                    row["valid_traceroute"],
                    row["traceroute"],
                    row["server"])

            l = "{},{}" + ",{},\"{}\"" * 4 + "\n"
            l = l.format(
                row["server"], row["mac"],
                row["valid_traceroute_compress_embratel"],
                traceroute_compress_embratel_filter,
                row["valid_traceroute_compress_embratel_"
                    "without_last_hop_embratel"],
                traceroute_compress_embratel_without_last_hop_embratel_filter,
                row["valid_traceroute_without_embratel"],
                traceroute_without_embratel_filter,
                row["valid_traceroute"],
                traceroute_filter)
            f.write(l)


def print_macs_per_name_filtered(dt_start, dt_end, mac_node):
    # TODO: Probably deprecated

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
    # TODO: Probably deprecated

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
    # TODO: Probably deprecated

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
    # TODO: Probably deprecated

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
    print_traceroute_per_mac(dt_start, dt_end)

    print_traceroute_per_mac_filtered(dt_start, dt_end)
    # print_macs_per_name_filtered(dt_start, dt_end, mac_node)


def run_sequential():
    mac_node = read_input.get_mac_node()
    for dt_start, dt_end in utils.iter_dt_range():
        print_all(dt_start, dt_end, mac_node)


def run_parallel():
    mac_node = read_input.get_mac_node()
    dt_ranges = list(utils.iter_dt_range())
    f_print_all = functools.partial(print_all, mac_node=mac_node)
    utils.parallel_exec(f_print_all, dt_ranges)


def run_single(dt_start, dt_end):
    mac_node = read_input.get_mac_node()
    print_all(dt_start, dt_end, mac_node)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
