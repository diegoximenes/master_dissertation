import os
import sys
import datetime
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils


def include_in_dataset(row):
    if (row["valid_cnt_samples"] and
            (row["valid_traceroute_compress_embratel"] or
             row["valid_traceroute_compress_embratel_"
                 "without_last_hop_embratel"] or
             row["valid_traceroute_without_embratel"])):
        return True
    return False


def create_dataset_unsupervised(dt_start, dt_end):
    """
    all [dt_start, dt_end) must be in the same month.
    datetimes must represent days
    """

    str_dt = utils.get_str_dt(dt_start, dt_end)
    utils.create_dirs(["{}/change_point/input/unsupervised/".format(base_dir),
                       "{}/change_point/input/unsupervised/{}".
                       format(base_dir, str_dt)])

    out_path = "{}/unsupervised/{}/dataset.csv".format(script_dir, str_dt)
    with open(out_path, "w") as f:
        f.write("email,mac,server,dt_start,dt_end,change_points,"
                "change_points_ids\n")

        in_path = ("{}/change_point/unsupervised/prints/{}/filtered/"
                   "traceroute_per_mac.csv".format(base_dir, str_dt))
        df = pd.read_csv(in_path)
        for idx, row in df.iterrows():
            if include_in_dataset(row):
                f.write("{},{},{},{},{},\"\",\"\"\n".format(str_dt,
                                                            row["mac"],
                                                            row["server"],
                                                            dt_start,
                                                            dt_end))


def run_parallel():
    dt_ranges = list(utils.iter_dt_range())
    utils.parallel_exec(create_dataset_unsupervised, dt_ranges)


def run_sequential():
    for dt_start, dt_end in utils.iter_dt_range():
        create_dataset_unsupervised(dt_start, dt_end)


def run_single(dt_start, dt_end):
    create_dataset_unsupervised(dt_start, dt_end)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
