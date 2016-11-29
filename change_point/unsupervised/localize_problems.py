import os
import sys
import datetime

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils as cp_utils


def localize_problems(dt_start, dt_end):
    str_dt = utils.get_str_dt(dt_start, dt_end)

    mac_traceroute = cp_utils.get_mac_traceroute_filtered(dt_start, dt_end)


def run_single(dt_start, dt_end):
    localize_problems(dt_start, dt_end)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    run_single(dt_start, dt_end)
    # run_parallel()
    # run_sequential()
