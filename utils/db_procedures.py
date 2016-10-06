import os
import dt_procedures


def valid_doc(doc):
    # check mac, date existence
    if (("_id" not in doc) or ("mac" not in doc["_id"]) or
            ("date" not in doc["_id"])):
        return False

    # check server(host), carrier(ISP), uf(client uf), huf(server uf) existence
    if (("host" not in doc) or ("carrier" not in doc) or
            ("uf" not in doc) or ("huf" not in doc)):
        return False

    if doc["carrier"] != "NET":
        return False

    # client and server must have the same uf
    if doc["uf"] != doc["huf"]:
        return False

    return True


def valid_doc_loss(doc):
    # check loss existence
    if (("rtt" not in doc) or ("loss" not in doc["rtt"]) or
            ("lat" not in doc["rtt"])):
        return False

    loss = float(doc["rtt"]["loss"])
    # there are some inconsistencies in the database
    if (loss < 0) or (loss > 1):
        return False
    if (loss < 1) and ("s" not in doc["rtt"]["lat"]):
        return False

    return True


def valid_doc_traceroute(doc):
    if (("tcrt" not in doc) or ("hops" not in doc["tcrt"])):
        return False
    return True


def get_data_to_file(cursor, out_dir_path):
    server_mac_dtMeasuresUf = {}

    cnt = 0
    for doc in cursor:
        cnt += 1
        print cnt

        if (not valid_doc(doc)) or (not valid_doc_loss(doc)):
            continue

        mac = doc["_id"]["mac"]
        uf = doc["uf"]
        server = doc["host"]
        dt = dt_procedures.from_utc_to_sp(doc["_id"]["date"])
        loss = float(doc["rtt"]["loss"])

        if valid_doc_traceroute(doc):
            traceroute = doc["tcrt"]["hops"]
        else:
            traceroute = None

        if server not in server_mac_dtMeasuresUf:
            server_mac_dtMeasuresUf[server] = {}
        if mac not in server_mac_dtMeasuresUf[server]:
            server_mac_dtMeasuresUf[server][mac] = []
        server_mac_dtMeasuresUf[server][mac].append([dt, uf, loss, traceroute])

    if not os.path.exists(out_dir_path):
        os.makedirs(out_dir_path)
    for server in server_mac_dtMeasuresUf:
        if not os.path.exists("{}/{}".format(out_dir_path, server)):
            os.makedirs("{}/{}".format(out_dir_path, server))

        for mac in server_mac_dtMeasuresUf[server]:
            server_mac_dtMeasuresUf[server][mac].sort()

            with open("{}/{}/{}.csv".format(out_dir_path, server, mac), "w") \
                    as f:
                f.write("dt,uf,loss,traceroute\n")
                for t in server_mac_dtMeasuresUf[server][mac]:
                    f.write("{},{},{},{}\n".format(*t))
