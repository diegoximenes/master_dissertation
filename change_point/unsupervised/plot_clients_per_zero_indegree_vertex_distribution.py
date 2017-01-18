import sys
import os
import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils
import change_point.unsupervised.spatial_time_correlation as \
    spatial_time_correlation


def plot_clients_per_zero_indegree_vertex_distribution(dt_start, dt_end):
    cnt_clients_zero_indegree_vertex = []

    str_dt = utils.get_str_dt(dt_start, dt_end)
    for server in os.listdir("{}/prints/{}/filtered/graph".
                             format(script_dir, str_dt)):
        for traceroute_type in unsupervised_utils.iter_traceroute_types():
            if spatial_time_correlation.valid_graph(dt_start, dt_end,
                                                    server,
                                                    traceroute_type):
                g = spatial_time_correlation.read_graph(dt_start, dt_end,
                                                        server,
                                                        traceroute_type)
                u_indegree = spatial_time_correlation.get_indegree(g)

                for u in g:
                    if u_indegree[u] == 0:
                        in_path = ("{}/plots/names/{}/latency/{}/{}/{}/"
                                   "cps_per_mac.csv".
                                   format(script_dir, str_dt,
                                          traceroute_type, server, u))
                        df = pd.read_csv(in_path)
                        cnt_clients_zero_indegree_vertex.append(
                            df.shape[0])
                break

    print sum(cnt_clients_zero_indegree_vertex)

    out_path = ("{}/plots/cnt_clients_zero_indegree_vertex_distribution.png".
                format(script_dir))
    plt.clf()
    matplotlib.rcParams.update({"font.size": 27})
    plt.gcf().set_size_inches(16, 11)
    bins = range(1, max(cnt_clients_zero_indegree_vertex) + 2)
    weights = (np.asarray([1.0] * len(cnt_clients_zero_indegree_vertex)) /
               len(cnt_clients_zero_indegree_vertex))
    plt.ylabel("frequency")
    plt.xlabel("number of clients in a zero indegree user-group")
    plt.xticks(bins[:-1], rotation=45)
    plt.hist(cnt_clients_zero_indegree_vertex, bins=bins, normed=True,
             weights=weights)
    plt.savefig(out_path)


if __name__ == "__main__":
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)

    plot_clients_per_zero_indegree_vertex_distribution(dt_start, dt_end)
