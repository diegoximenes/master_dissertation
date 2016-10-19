import os
import sys
import ast
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.utils.cmp_class as cmp_class
import utils.dt_procedures as dt_procedures
from utils.time_series import TimeSeries


def match(date_dir, delta_hours=10):
    in_path = "{}/prints/{}/predicted_cps_per_mac.csv".format(script_dir,
                                                              date_dir)

    mac_cps = {}
    mac_server = {}
    mac_node = {}
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        strdts = ast.literal_eval(row["cp_dt"])
        dts = []
        for strdt in strdts:
            dts.append(dt_procedures.from_strdt_to_dt(strdt))
        mac_cps[row["mac"]] = dts
        mac_server[row["mac"]] = row["server"]
        mac_node[row["mac"]] = row["node"]

    out_path = "{}/prints/{}/cp_dt_matches.csv".format(script_dir, date_dir)
    with open(out_path, "w") as f:
        f.write("server1,server2,node1,node2,mac1,mac2,tp,fp\n")
        for mac1 in mac_cps:
            for mac2 in mac_cps:
                if mac1 != mac2:
                    # only tp, fp are correct with this parameters
                    win_delta = datetime.timedelta(hours=delta_hours)
                    ts = TimeSeries()
                    conf = cmp_class.conf_mat(mac_cps[mac1], mac_cps[mac2], ts,
                                              win_delta)
                    formatter = "{}" + ",{}" * 7 + "\n"
                    f.write(formatter.format(mac_server[mac1],
                                             mac_server[mac2],
                                             mac_node[mac1],
                                             mac_node[mac2],
                                             mac1,
                                             mac2,
                                             conf["tp"],
                                             conf["fp"]))

    # sort file
    df = pd.read_csv(out_path)
    df_sorted = df.sort(["tp", "server1", "node1", "server2", "node2", "mac1",
                         "mac2"],
                        ascending=[False] + [True] * 6)
    df_sorted.to_csv(out_path, index=False)


if __name__ == "__main__":
    date_dir = "2016_06"
    match(date_dir)
