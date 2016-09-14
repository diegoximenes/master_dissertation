import os
import pandas as pd


def stats():
    in_dir = "../../input/2016_05/"

    cnt_servers = 0
    cnt_clients = 0
    cnt_measures = 0
    for server in os.listdir(in_dir):
        cnt_servers += 1
        for file_name in os.listdir("{}/{}".format(in_dir, server)):
            cnt_clients += 1
            df = pd.read_csv("{}/{}/{}".format(in_dir, server, file_name))
            cnt_measures += df.shape[0]

    with open("./basic_statistics.out", "w") as f:
        f.write("cnt_servers={}\n".format(cnt_servers))
        f.write("cnt_clients={}\n".format(cnt_clients))
        f.write("cnt_measures={}\n".format(cnt_measures))


if __name__ == "__main__":
    stats()
