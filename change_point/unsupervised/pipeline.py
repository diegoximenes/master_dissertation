import sys
import os
import datetime

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.cp_utils.cmp_win as cmp_win
import change_point.unsupervised.traceroute_exploratory_prints as \
    traceroute_exploratory_prints
import change_point.unsupervised.print_graph as print_graph
import change_point.input.create_dataset_unsupervised as \
    create_dataset_unsupervised
import change_point.unsupervised.print_cps as print_cps
import change_point.unsupervised.voting as voting
import change_point.unsupervised.analyse_vertexes_with_zero_in_degree as \
    analyse_vertexes_with_zero_in_degree
import change_point.unsupervised.plot_names as plot_names
import change_point.unsupervised.plot_paths as plot_paths
import change_point.models.sliding_windows.sliding_windows_offline as \
    sliding_windows_offline


def myprint(s):
    sys.stdout = sys.__stdout__
    print s
    sys.stdout = open(os.devnull, "w")


if __name__ == "__main__":
    ############################
    # PARAMETERS
    ############################
    dt_start = datetime.datetime(2016, 6, 21)
    dt_end = datetime.datetime(2016, 7, 1)

    metric = "latency"
    dir_model = "sliding_windows/offline"
    hours_tol = 4
    filtered = "filtered"

    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 21,
                       "p": 0.5}
    param = {"win_len": 48,
             "thresh": 3,
             "min_peak_dist": 18,
             "f_dist": cmp_win.mean_dist,
             "bin_size_f_dist": 0.05,
             "min_bin_f_dist": 0.0,
             "max_bin_f_dist": 1.0}
    ############################

    sys.stdout = open(os.devnull, "w")

    myprint("traceroute_exploratory_prints")
    traceroute_exploratory_prints.run_parallel()

    myprint("print_graph")
    print_graph.run_parallel()

    myprint("create_dataset_unsupervised")
    create_dataset_unsupervised.run_parallel()

    myprint("sliding_windows_offline")
    sliding_windows_offline.run_parallel(cmp_class_args, preprocess_args,
                                         param, metric)

    myprint("print_cps")
    print_cps.run_parallel(dir_model, metric, filtered)

    myprint("voting")
    voting.run_parallel(metric, hours_tol)

    myprint("analyse_vertexes_with_zero_in_degree")
    analyse_vertexes_with_zero_in_degree.run_parallel(metric, hours_tol)

    myprint("plot_names")
    plot_names.run_parallel(metric)

    myprint("plot_paths")
    plot_paths.run_parallel(metric)

    sys.stdout = sys.__stdout__
