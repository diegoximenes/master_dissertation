import sys
import os

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.unsupervised.traceroute_exploratory_prints as \
    traceroute_exploratory_prints
import change_point.unsupervised.print_graph as print_graph
import change_point.input.create_dataset_unsupervised as \
    create_dataset_unsupervised
import change_point.unsupervised.print_cps as print_cps
import change_point.unsupervised.time_correlation as time_correlation
import change_point.unsupervised.spatial_time_correlation as \
    spatial_time_correlation
import change_point.unsupervised.plot_names as plot_names
import change_point.unsupervised.plot_paths as plot_paths
import change_point.models.seg_neigh.seg_neigh as seg_neigh
import change_point.unsupervised.plot_latencies_traceroute as \
    plot_latencies_traceroute
import change_point.models.change_point_alg as change_point_alg


def myprint(s):
    sys.stdout = sys.__stdout__
    print s
    sys.stdout = open(os.devnull, "w")


def get_change_point_alg_params(metric, dir_model, hours_tol):
    if metric == "latency":
        preprocess_args = {"filter_type": "percentile_filter",
                           "win_len": 13,
                           "p": 0.5}
    elif metric == "loss":
        preprocess_args = {"filter_type": "percentile_filter",
                           "win_len": 5,
                           "p": 0.5}
    elif metric == "throughput_up":
        preprocess_args = {"filter_type": "percentile_filter",
                           "win_len": 13,
                           "p": 0.5}

    if dir_model == "seg_neigh":
        if metric == "latency":
            param = {"const_pen": 100,
                     "f_pen": "n_cps ^ 2",
                     "seg_model": "Normal",
                     "min_seg_len": hours_tol * 2 + 1,
                     "max_cps": 6}
        elif metric == "loss":
            param = {"const_pen": 200,
                     "f_pen": "n_cps",
                     "seg_model": "Normal",
                     "min_seg_len": hours_tol * 2 + 1,
                     "max_cps": 6}
        elif metric == "throughput_up":
            param = {"const_pen": 200,
                     "f_pen": "n_cps",
                     "seg_model": "Normal",
                     "min_seg_len": hours_tol * 2 + 1,
                     "max_cps": 6}

    return preprocess_args, param


if __name__ == "__main__":
    ############################
    # CHANGE POINT DETECTION PARAMETERS
    ############################
    metric = "loss"
    dir_model = "seg_neigh"
    hours_tol = 12

    cmp_class_args = {"win_len": 15}
    preprocess_args, param = get_change_point_alg_params(metric, dir_model,
                                                         hours_tol)

    min_fraction_of_clients = 0.85
    ############################

    sys.stdout = open(os.devnull, "w")

    # myprint("traceroute_exploratory_prints")
    # traceroute_exploratory_prints.run_parallel()
    #
    # myprint("print_graph")
    # print_graph.run_parallel()
    #
    # myprint("create_dataset_unsupervised")
    # create_dataset_unsupervised.run_parallel()
    #
    myprint("change_point_alg")
    change_point_alg.run_parallel(cmp_class_args, preprocess_args, param,
                                  metric, seg_neigh.run)

    myprint("print_cps")
    print_cps.run_parallel(dir_model, metric, preprocess_args)

    myprint("time_correlation")
    time_correlation.run_parallel(metric, hours_tol)

    # myprint("spatial_time_correlation")
    # spatial_time_correlation.run_parallel(metric, hours_tol,
    #                                       min_fraction_of_clients)

    # myprint("plot_names")
    # plot_names.run_parallel(metric, preprocess_args)

    myprint("plot_paths")
    plot_paths.run_parallel(metric, preprocess_args)

    if metric == "latency":
        myprint("plot_latencies_traceroute")
        plot_latencies_traceroute.run_parallel(preprocess_args)

    sys.stdout = sys.__stdout__
