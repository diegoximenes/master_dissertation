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


def get_macs(cursor):
    """
    only consider clients that measured against a single server in the cursor
    documents. Returns a list with the macs and another one with the associated
    servers
    """

    mac_servers = {}
    cnt = 0
    for doc in cursor:
        cnt += 1
        print "db_procedures.get_macs, cnt={}".format(cnt)

        if not valid_doc(doc):
            continue

        mac = doc["_id"]["mac"]
        server = doc["host"]

        if mac not in mac_servers:
            mac_servers[mac] = set()
        mac_servers[mac].add(server)

    macs = []
    servers = []
    for mac in mac_servers:
        if len(mac_servers[mac]) == 1:
            macs.append(mac)
            servers.append(mac_servers[mac].pop())
    return macs, servers
