import os
import sys
import pandas as pd

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)

script_dir = os.path.join(os.path.dirname(__file__), ".")


def filter_names(names):
    names_ret = []
    return names_ret


def filter(date_dir):
    out_path = "{}/prints/{}/names_per_mac_filtered.csv".format(script_dir,
                                                                date_dir)
    with open(out_path, "w") as f:
        f.write("server,mac,names\n")
        in_path = "{}/prints/{}/names_per_mac.csv".format(script_dir, date_dir)
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            f.write("{},{},\"{}\"\n".format(row["server"], row["mac"],
                                            filter_names(row["names"])))


if __name__ == "__main__":
    date_dirs = ["2016_06"]

    for date_dir in date_dirs:
        filter(date_dir)
