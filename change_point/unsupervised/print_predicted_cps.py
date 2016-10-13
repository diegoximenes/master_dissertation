import os
import sys
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.read_input as read_input


def create_dirs(date_dir):
    for dir in ["{}/prints".format(script_dir),
                "{}/prints/{}".format(script_dir, date_dir)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def get_unique_traceroute():
    mac_traceroute = {}
    df = pd.read_csv("{}/prints/2016_06/traceroute_per_mac_filtered.csv".
                     format(script_dir))
    for idx, row in df.iterrows():
        mac_traceroute[row["mac"]] = row["traceroute"]
    return mac_traceroute


def print_predicted_cps(pred_dir, dt_start, dt_end):
    """
    []dt_start, dt_end) must define a month
    """

    dt_end = dt_end - datetime.timedelta(days=1)

    mac_node = read_input.get_mac_node()
    mac_traceroute = get_unique_traceroute()

    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))
    create_dirs(date_dir)
    out_path = "{}/prints/{}/predicted_cps_per_mac.csv".format(script_dir,
                                                               date_dir)

    with open(out_path, "w") as f:
        f.write("server,node,mac,cp_dt,traceroute\n")
        for file_name in os.listdir(pred_dir):
            if file_name.split(".")[-1] == "csv":
                server = file_name.split("server")[1].split("_")[0]
                mac = file_name.split("mac")[1].split("_")[0]
                df = pd.read_csv("{}/{}".format(pred_dir, file_name))

                dts = []
                for idx, row in df.iterrows():
                    dts.append(row["dt"])
                dts.sort()

                f.write("{},{},{},\"{}\",\"{}\"\n".
                        format(server, mac_node.get(mac), mac, dts,
                               mac_traceroute.get(mac)))

    # sort file
    df = pd.read_csv(out_path)
    df_sorted = df.sort(["server", "node", "mac"],
                        ascending=[True, True, True])
    df_sorted.to_csv(out_path, index=False)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 7, 1)

    dt_end = dt_end - datetime.timedelta(days=1)
    dataset = "unsupervised/unsupervised_dtstart{}_dtend{}".format(dt_start,
                                                                   dt_end)
    pred_dir = ("{}/change_point/models/sliding_windows/plots/{}/offline".
                format(base_dir, dataset))

    print_predicted_cps(pred_dir, dt_start, dt_end)
