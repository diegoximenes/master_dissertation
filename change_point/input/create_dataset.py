import os
import sys
import math
import random
import shutil
import numpy as np
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
from utils.time_series import TimeSeries
import utils.dt_procedures as dt_procedures


def split_train_test(target_email):
    in_path = "{}/{}/dataset.csv".format(script_dir, target_email)
    train_size = 0.7

    test_size = 1 - train_size
    df = pd.read_csv(in_path)

    idxs = np.arange(len(df))
    random.shuffle(idxs)

    df_train = df.iloc[idxs[0:int(math.ceil(train_size * len(df)))]]
    df_test = df.iloc[idxs[len(df_train):len(df_train) +
                           int(math.ceil(test_size * len(df)))]]

    df_train.to_csv("{}/{}/train.csv".format(script_dir, target_email),
                    index_label="id_dataset")
    df_test.to_csv("{}/{}/test.csv".format(script_dir, target_email),
                   index_label="id_dataset")


def create_dataset(target_email):
    in_path = "{}/{}/data_web_system.csv".format(script_dir, target_email)
    df = pd.read_csv(in_path)
    df_ret = df[df["email"] == target_email]
    df_ret.to_csv("{}/{}/dataset.csv".format(script_dir, target_email),
                  index=False)


def from_dt_to_id(in_path, metric, dt_start, dt_end, l_dt):
    """
    return ids associated with dts in l_dt list
    """
    ts = TimeSeries(in_path, metric, dt_start=dt_start, dt_end=dt_end)

    dt_id = {}
    for i in xrange(len(ts.x)):
        dt_id[ts.x[i]] = i

    l_id = []
    for dt in l_dt:
        l_id.append(dt_id[dt])
    return l_id


def add_cp_ids(target_email):
    """
    write to in_path a new column: the change points ids (index of change
    points when points are sorted by measure datetime)
    """

    in_path = "{}/{}/data_web_system.csv".format(script_dir, target_email)
    df = pd.read_csv(in_path, sep=";")
    if "change_points_ids" not in df:
        cp_ids = []
        for idx, row in df.iterrows():
            dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
            dt_end = dt_procedures.from_js_strdate_to_dt(row["date_end"])
            date_dir = "{}_{}".format(dt_start.year,
                                      str(dt_start.month).zfill(2))
            in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir,
                                                     row["server"], row["mac"])
            if str(row["change_points"]) != "\'\'":
                l_dt = map(dt_procedures.from_js_strdt_to_dt,
                           row["change_points"].split(","))
                l_id = from_dt_to_id(in_path, "loss", dt_start, dt_end, l_dt)
                cp_ids.append(",".join(map(str, l_id)))
            else:
                cp_ids.append("")
        df["change_points_ids"] = cp_ids
        df.to_csv("{}/{}/data_web_system.csv".format(script_dir, target_email),
                  index=False)


def create_dirs(target_email):
    for dir in ["{}/change_point/input/{}".format(base_dir, target_email)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


if __name__ == "__main__":
    for target_email in ["gabriel.mendonca@tgr.net.br",
                         "gustavo.santos@tgr.net.br",
                         "rosam@land.ufrj.br",
                         "guisenges@land.ufrj.br",
                         "edmundo@land.ufrj.br"]:
        create_dirs(target_email)
        shutil.copyfile("{}/change_point/from_unsupervised_to_supervised/"
                        "classifications.csv".format(base_dir),
                        "{}/change_point/input/{}/data_web_system.csv"
                        "".format(base_dir, target_email))
        add_cp_ids(target_email)
        create_dataset(target_email)
        split_train_test(target_email)
