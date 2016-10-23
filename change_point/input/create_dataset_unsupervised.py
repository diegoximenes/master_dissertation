import os
import sys
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
from utils.time_series import TimeSeries


def include_in_dataset(ts, mac, dt_dir, dt_start, dt_end,
                       min_samples_fraction=0.5):
    df = pd.read_csv("{}/change_point/unsupervised/prints/{}/"
                     "traceroute_per_mac_filtered.csv".format(base_dir,
                                                              dt_dir))
    if mac not in df["mac"].values:
        return False

    delta_days = (dt_end - dt_start).days
    if float(len(ts.y)) / (delta_days * 24.0 * 2.0) < min_samples_fraction:
        return False

    return True


def create_dataset_unsupervised(dt_start, dt_end):
    """
    all [dt_start, dt_end) must be in the same month.
    datetimes must represent days
    """

    dt_dir = utils.get_dt_dir(dt_start, dt_end)
    utils.create_dirs(["{}/change_point/input/unsupervised/".format(base_dir),
                       "{}/change_point/input/unsupervised/{}".
                       format(base_dir, dt_dir)])

    js_date_start = "{}/{}/{}".format(str(dt_start.month).zfill(2),
                                      str(dt_start.day).zfill(2),
                                      dt_start.year)
    # js dates are kept in interval like [dt_start, dt_end] instead of
    # [dt_start, dt_end)
    dt_end_correction = dt_end - datetime.timedelta(days=1)
    js_date_end = "{}/{}/{}".format(str(dt_end_correction.month).zfill(2),
                                    str(dt_end_correction.day).zfill(2),
                                    dt_end_correction.year)

    out_path = "{}/unsupervised/{}/dataset.csv".format(script_dir, dt_dir)
    with open(out_path, "w") as f:
        f.write("email,mac,server,date_start,date_end,change_points,"
                "change_points_ids\n")
        for server, mac, in_path in utils.iter_server_mac(dt_dir, True):
            ts = TimeSeries(in_path, "loss", dt_start, dt_end)
            if include_in_dataset(ts, mac, dt_dir, dt_start, dt_end):
                f.write("{},{},{},{},{},\"\",\"\"\n".format(dt_dir, mac,
                                                            server,
                                                            js_date_start,
                                                            js_date_end))


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 1)
    dt_end = datetime.datetime(2016, 7, 1)
    create_dataset_unsupervised(dt_start, dt_end)
