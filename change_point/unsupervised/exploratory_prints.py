import os
import sys
import ast
import copy
import socket
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)


def create_dirs(date_dir):
    for dir in ["{}/prints".format(script_dir),
                "{}/prints/{}".format(script_dir, date_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def iter_mac(date_dir):
    in_dir = "{}/input/{}/".format(base_dir, date_dir)
    cnt = 0
    for server in os.listdir(in_dir):
        for file_name in os.listdir("{}/{}".format(in_dir, server)):
            cnt += 1
            print "cnt={}".format(cnt)

            mac = file_name.split(".csv")[0]
            print "mac={}, server={}".format(mac, server)

            df = pd.read_csv("{}/{}/{}".format(in_dir, server, file_name))
            yield server, mac, df


def valid_ip(str_ip):
    try:
        socket.inet_aton(str_ip)
        return True
    except socket.error:
        return False


def from_str_to_traceroute(str_traceroute):
    str_traceroute = str_traceroute.replace("nan", "None")
    return ast.literal_eval(str_traceroute)


def get_ip_name(traceroute):
    """
    get the ip->name mapping:
    the dns resolution can fail, and the ip can be
    displayed at the "names" field
    """

    ip_name = {}
    for hop in traceroute:
        for ip, name in zip(hop["ips"], hop["names"]):
            if ((name != u"##") and ((ip not in ip_name) or
                                     (not valid_ip(name)))):
                ip_name[ip] = name
    return ip_name


def get_name(name, ip_name):
    if not valid_ip(name):
        return name
    else:
        # name is an ip
        if name in ip_name:
            return ip_name[name]
        else:
            return None


def get_mac_node():
    mac_node = {}
    df = pd.read_csv("{}/input/probes_info.csv".format(base_dir), sep=" ")
    for idx, row in df.iterrows():
        mac_node[row["MAC_ADDRESS"]] = row["NODE"]
    return mac_node


def get_node(mac, mac_node):
    if mac in mac_node:
        return mac_node[mac]
    return None


def get_traceroute(df):
    hops_default = []
    for idx, row in df.iterrows():
        traceroute = from_str_to_traceroute(row["traceroute"])

        # THIS PIECE OF CODE EXPOSES A TRACEROUTE INCONSISTENCY
        # IN 2016_06
        # if traceroute is not None:
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

        if traceroute is not None:
            ip_name = get_ip_name(traceroute)

            hops = []
            for hop in traceroute:
                # get a single name for each hop
                hop_name = None
                for name in hop["names"]:
                    if (name != u"##"):
                        hop_name = get_name(name, ip_name)

                # check if more than one name appear in the
                # same hop
                for name in hop["names"]:
                    if ((name != u"##") and
                            (hop_name != get_name(name, ip_name))):
                        return False, "diff_name_same_hop={}".format(hop)

                hops.append(hop_name)

            if not hops_default:
                hops_default = copy.deepcopy(hops)
            else:
                update_hops_default = False
                for name_hops, name_hops_default in zip(hops, hops_default):
                    if ((name_hops is not None) and
                            (name_hops_default is None)):
                        # current traceroute have more
                        # information than previous ones
                        update_hops_default = True
                    elif ((name_hops is not None) and
                          (name_hops_default is not None) and
                          (name_hops != name_hops_default)):
                        # different traceroutes
                        return False, "hops1={}, hops2={}".format(hops,
                                                                  hops_default)

                if update_hops_default:
                    hops_default = copy.deepcopy(hops)

    return True, "unique={}".format(hops_default)


def filter_names(names):
    names_filtered = []
    return names_filtered


def print_lines(f, lines):
        lines.sort()
        for line in lines:
            f.write(line)


def print_traceroute_per_mac(date_dir, mac_node):
    out_path = "{}/prints/{}/traceroutes.csv".format(script_dir, date_dir)
    with open(out_path, "w") as f:
        f.write("server,node,mac,traceroute\n")
        lines = []
        last_server = None
        for server, mac, df in iter_mac(date_dir):
            if (last_server is not None) and (server != last_server):
                print_lines(f, lines)
                lines = []
            last_server = server
            unique_traceroute, str_traceroute = get_traceroute(df)
            node = get_node(mac, mac_node)
            lines.append("{},{},{},\"{}\"\n".format(server, node, mac,
                                                    str_traceroute))


def print_name_ips(date_dir):
    name_ip = {}
    for _, _, df in iter_mac(date_dir):
        for idx, row in df.iterrows():
            traceroute = from_str_to_traceroute(row["traceroute"])
            if traceroute is not None:
                for hop in traceroute:
                    for name, ip in zip(hop["names"], hop["ips"]):
                        if name not in name_ip:
                            name_ip[name] = set()
                        name_ip[name].add(ip)

    out_path = "{}/prints/{}/name_ips.csv".format(script_dir, date_dir)
    with open(out_path, "w") as f:
        f.write("name,ips\n")
        for name in sorted(name_ip.keys()):
            f.write("{},{}\n".format(name, sorted(list(name_ip[name]))))


def print_names_per_mac(date_dir, mac_node):
    out_path = "{}/prints/{}/names_per_mac.csv".format(script_dir, date_dir)
    with open(out_path, "w") as f:
        f.write("server,node,mac,names\n")
        lines = []
        last_server = None
        for server, mac, df in iter_mac(date_dir):
            if (last_server is not None) and (server != last_server):
                print_lines(f, lines)
                lines = []
            last_server = server

            names = set()
            for idx, row in df.iterrows():
                traceroute = from_str_to_traceroute(row["traceroute"])
                if traceroute is not None:
                    ip_name = get_ip_name(traceroute)
                    for hop in traceroute:
                        for name in hop["names"]:
                            names.add(get_name(name, ip_name))
            node = get_node(mac, mac_node)
            lines.append("{},{},{},\"{}\"\n".format(server, node, mac,
                                                    sorted(list(names))))


def print_names_per_mac_filtered(date_dir):
    out_path = "{}/prints/{}/names_per_mac_filtered.csv".format(script_dir,
                                                                date_dir)
    with open(out_path, "w") as f:
        f.write("server,mac,names\n")
        in_path = "{}/prints/{}/names_per_mac.csv".format(script_dir, date_dir)
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            names = ast.literal_eval(row["names"])
            names_filtered = filter_names(names)
            f.write("{},{},{},\"{}\",\"{}\"\n".format(row["server"],
                                                      row["node"],
                                                      row["mac"],
                                                      row["names"],
                                                      names_filtered))


def print_macs_per_name(date_dir, mac_node):
    name_macs = {}
    for server, mac, df in iter_mac(date_dir):
        for idx, row in df.iterrows():
            traceroute = from_str_to_traceroute(row["traceroute"])
            if traceroute is not None:
                ip_name = get_ip_name(traceroute)
                for hop in traceroute:
                    for name in hop["names"]:
                        name = get_name(name, ip_name)
                        if name not in name_macs:
                            name_macs[name] = set()
                        name_macs[name].add((server, get_node(mac, mac_node),
                                             mac))

    out_path = "{}/prints/{}/macs_per_name.csv".format(script_dir, date_dir)
    with open(out_path, "w") as f:
        f.write("name,macs\n")
        names = sorted(name_macs.keys())
        for name in names:
            f.write("{},\"{}\"\n".format(name, sorted(list(name_macs[name]))))


if __name__ == "__main__":
    # not all dirs have csv's with traceroute
    date_dirs = ["2016_06"]

    mac_node = get_mac_node()
    for date_dir in date_dirs:
        create_dirs(date_dir)

        print_names_per_mac_filtered(date_dir)
        # print_macs_per_name(date_dir, mac_node)
        # print_names_per_mac(date_dir, mac_node)
        # print_name_ips(date_dir)
        # print_traceroute_per_mac(date_dir, mac_node)