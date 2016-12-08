import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)


if __name__ == "__main__":
    metric = "latency"
    for str_dt in os.listdir("{}/plots/names".format(script_dir)):
        dir_path = "{}/plots/names/{}/{}".format(script_dir, str_dt, metric)
        for server in os.listdir(dir_path):
            in_path = "{}/{}/problem_correlation.csv".format(dir_path, server)
            if os.path.isfile(in_path):
                df = pd.read_csv(in_path)
                for idx, row in df.iterrows():
                    if row["cnt_vertexes_with_zero_in_deg"] > 1:
                        print "str_dt={}, server={}".format(str_dt, server)
