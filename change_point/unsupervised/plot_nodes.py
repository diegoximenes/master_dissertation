import sys
import os
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries


def create_dirs(date_dir, node):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/nodes".format(script_dir, date_dir),
                "{}/plots/nodes/{}".format(script_dir, date_dir),
                "{}/plots/nodes/{}/{}".format(script_dir, date_dir, node)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def plot(dt_start, dt_end):
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))

    df = pd.read_csv("{}/prints/valid_nodes.csv".format(script_dir))
    valid_nodes = set()
    for idx, row in df.iterrows():
        valid_nodes.add(row["node"])

    mac_node = {}
    df = pd.read_csv("{}/input/probes_info.csv".format(base_dir), sep=" ")
    for idx, row in df.iterrows():
        mac_node[row["MAC_ADDRESS"]] = row["NODE"]

    for server in os.listdir("{}/input/{}".format(base_dir, date_dir)):
        for file_name in os.listdir("{}/input/{}/{}/".format(base_dir,
                                                             date_dir,
                                                             server)):
            mac = file_name.split(".csv")[0]
            if mac_node[mac] in valid_nodes:
                create_dirs(date_dir, mac_node[mac])

                in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir,
                                                         server, mac)
                out_path = "{}/plots/nodes/{}/{}/{}.png".format(script_dir,
                                                                date_dir,
                                                                mac_node[mac],
                                                                mac)
                ts = TimeSeries(in_path, "loss", dt_start, dt_end)
                plot_procedures.plot_ts(ts, out_path, ylim=[-0.02, 1.02])

if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 7, 1)
    dt_end = datetime.datetime(2016, 8, 1)
    plot(dt_start, dt_end)
