import os
import sys
import datetime
import functools
import ast
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.cp_utils.cp_utils as cp_utils


def problem_location(dt_start, dt_end):
    def problem_before(in_path):
        df = pd.read_csv(in_path)
        cnt_all = df.shape[0]
        df_before = df[df["problem_location"] == "['before']"]
        cnt_before = df_before.shape[0]
        df_before = df[df["cnt_clients"] > 1]
        cnt_before_more_than_one_client = df_before.shape[0]
        return cnt_all, cnt_before, cnt_before_more_than_one_client

    str_dt = utils.get_str_dt(dt_start, dt_end)

    out_path = "{}/prints/{}/filtered/problem_location_statistics.csv".format(
        script_dir, str_dt)
    with open(out_path) as f:
        f.write("cnt_all,"
                "cnt_before,"
                "cnt_before_more_than_one_client,"
                "cnt_not_before,"
                "cnt_not_before_more_than_one_zero_indegree_vertex\n")

        in_path = ("{}/prints/{}/filtered/{}/"
                   "problem_location_first_hop_not_zero_indegree_vertex.csv".
                   format(script_dir, str_dt, metric))
        df = pd.read_csv(in_path)
        df_before = df[df["problem_location"] == "['before']"]
        cnt_all = df_before.shape[0]
        cnt_before = df_before.shape[0]
        df_before = df[df["cnt_clients"] > 1]
        cnt_before_more_than_one_client = df_before.shape[0]

        in_path = ("{}/prints/{}/filtered/{}/"
                   "problem_location_zero_indegree_vertexes_correlation.csv".
                   format(script_dir, str_dt, metric))

        df = pd.read_csv(in_path)
        cnt_all += df.shape[0]
        df = df[df["problem_location"] == "['before']"]
        for _, row in df.iterrows():
            dic = ast.literal_eval(row["vertexes_with_zero_indegree"])
            cnt_before += 1
            if dic["cnt_clients"] > 1:
                cnt_before_more_than_one_client += 1

        df = pd.read_csv(in_path)
        df = df[df["problem_location"] != "['before']"]
        cnt_not_before = df.shape[0]
        df = df[df["cnt_vertexes_with_zero_indegree"] > 1]
        cnt_not_before_more_than_one_zero_indegree_vertex = df.shape[0]

        l = "{}" + ",{}" * 5
        l = l.format(cnt_all,
                     cnt_before,
                     cnt_before_more_than_one_client,
                     cnt_not_before,
                     cnt_not_before_more_than_one_zero_indegree_vertex)
        f.write(l)


def statistics(dt_start, dt_end, metric):
    problem_location(dt_start, dt_end, metric)


def run_sequential(metric, eps_hours):
    for dt_start, dt_end in utils.iter_dt_range():
        statistics(dt_start, dt_end, metric)


def run_parallel(metric, eps_hours):
    dt_ranges = list(utils.iter_dt_range())
    f_statistics = functools.partial(statistics, metric=metric)
    utils.parallel_exec(f_statistics, dt_ranges)


def run_single(dt_start, dt_end, metric):
    statistics(dt_start, dt_end, metric)


if __name__ == "__main__":
    metric = "latency"
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    parallel_args = {"metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start,
                   "dt_end": dt_end}
    single_args.update(parallel_args)
    cp_utils.parse_args(run_single, single_args,
                        run_parallel, parallel_args,
                        run_sequential, sequential_args,
                        None, None)
