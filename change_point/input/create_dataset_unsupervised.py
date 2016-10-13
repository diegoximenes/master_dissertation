import os
import sys
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
from utils.time_series import TimeSeries


def create_dirs(dataset):
    for dir in ["{}/change_point/input/unsupervised/".format(base_dir),
                "{}/change_point/input/unsupervised/{}".format(base_dir,
                                                               dataset)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def include_in_dataset(ts, mac, date_dir, dt_start, dt_end,
                       min_samples_fraction=0.5):
    df = pd.read_csv("{}/change_point/unsupervised/prints/{}/"
                     "traceroute_per_mac_filtered.csv".format(base_dir,
                                                              date_dir))
    if mac not in df["mac"].values:
        return False

    delta_days = (dt_end - dt_start).days + 1
    if float(len(ts.y)) / (delta_days * 24.0 * 2.0) < min_samples_fraction:
        return False

    return True


def create_dataset_unsupervised(dt_start, dt_end):
    """
    all [dt_start, dt_end) must be in the same month.
    datetimes must represent days
    """

    # adjust to time interval be defined by [dt_start, dt_end]
    dt_end = dt_end - datetime.timedelta(days=1)

    dataset = "unsupervised_dtstart{}_dtend{}".format(dt_start, dt_end)
    create_dirs(dataset)

    js_date_start = "{}/{}/{}".format(str(dt_start.month).zfill(2),
                                      str(dt_start.day).zfill(2),
                                      dt_start.year)
    js_date_end = "{}/{}/{}".format(str(dt_end.month).zfill(2),
                                    str(dt_end.day).zfill(2),
                                    dt_end.year)
    date_dir = "{}_{}".format(dt_start.year, str(dt_start.month).zfill(2))

    out_path = "{}/unsupervised/{}/dataset.csv".format(script_dir, dataset)
    with open(out_path, "w") as f:
        f.write("email,mac,server,date_start,date_end,change_points,"
                "change_points_ids\n")
        cnt = 0
        for server in os.listdir("{}/input/{}/".format(base_dir, date_dir)):
            for file_name in os.listdir("{}/input/{}/{}/".format(base_dir,
                                                                 date_dir,
                                                                 server)):
                cnt += 1
                print "cnt={}".format(cnt)

                mac = file_name.split(".csv")[0]
                in_path = "{}/input/{}/{}/{}".format(base_dir, date_dir,
                                                     server, file_name)
                ts = TimeSeries(in_path=in_path, metric="loss",
                                dt_start=dt_start, dt_end=dt_end)
                if include_in_dataset(ts, mac, date_dir, dt_start, dt_end):
                    f.write("{},{},{},{},{},\"\",\"\"\n".format(dataset, mac,
                                                                server,
                                                                js_date_start,
                                                                js_date_end))


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 7, 1)
    create_dataset_unsupervised(dt_start, dt_end)
