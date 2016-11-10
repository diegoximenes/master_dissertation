import os
import sys
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
from utils.time_series import TimeSeries


def include_in_dataset(ts, mac, dt_dir, str_dt, dt_start, dt_end,
                       min_samples_fraction=0.5, filtered="filtered"):
    df = pd.read_csv("{}/change_point/unsupervised/prints/{}/{}/"
                     "traceroute_per_mac.csv".format(base_dir, str_dt,
                                                     filtered))
    if mac not in df["mac"].values:
        return False

    # delta_days = (dt_end - dt_start).days
    # if float(len(ts.y)) / (delta_days * 24.0 * 2.0) < min_samples_fraction:
    #     return False

    return True


def create_dataset_unsupervised(dt_start, dt_end):
    """
    all [dt_start, dt_end) must be in the same month.
    datetimes must represent days
    """

    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    str_dt = utils.get_str_dt(dt_start, dt_end)
    utils.create_dirs(["{}/change_point/input/unsupervised/".format(base_dir),
                       "{}/change_point/input/unsupervised/{}".
                       format(base_dir, str_dt)])

    out_path = "{}/unsupervised/{}/dataset.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("email,mac,server,dt_start,dt_end,change_points,"
                "change_points_ids\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts = TimeSeries(in_path, "loss", dt_start, dt_end)
            if include_in_dataset(ts, mac, dt_dir, str_dt, dt_start, dt_end):
                f.write("{},{},{},{},{},\"\",\"\"\n".format(str_dt, mac,
                                                            server,
                                                            dt_start,
                                                            dt_end))


if __name__ == "__main__":
    # dt_start = datetime.datetime(2016, 7, 11)
    # dt_end = datetime.datetime(2016, 7, 21)
    # create_dataset_unsupervised(dt_start, dt_end)

    dt_ranges = list(utils.iter_dt_range())
    utils.parallel_exec(create_dataset_unsupervised, dt_ranges)

    # for dt_start, dt_end in utils.iter_dt_range():
    #     create_dataset_unsupervised(dt_start, dt_end)
