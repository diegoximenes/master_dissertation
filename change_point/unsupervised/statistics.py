import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


def problem_location_statistics():
    out_path = "{}/prints/problem_location_statistics.csv".format(script_dir)
    with open(out_path, "w") as f:
        f.write("metric,"
                "cp_type,"
                "cnt_before,"
                "cnt_zero_indegree_without_correlation,"
                "cnt_zero_indegree_with_correlation\n")

        for metric in ["latency", "loss", "throughput_up"]:
            for cp_type in cp_utils.iter_cp_types():
                in_path = ("{}/prints/"
                           "problem_location_first_hop_not_zero_indegree_"
                           "vertex.csv".format(script_dir))
                df = pd.read_csv(in_path)
                df = df[df["metric"] == metric]
                df = df[df["cp_type"] == cp_type]
                df_before = df[df["problem_location"] == "['before']"]
                cnt_before = df_before.shape[0]

                in_path = ("{}/prints/"
                           "problem_location_zero_indegree_vertexes_"
                           "correlation.csv".format(script_dir))
                df = pd.read_csv(in_path)
                df = df[df["metric"] == metric]
                df = df[df["cp_type"] == cp_type]
                df_before = df[df["suffix_match"] == "['before']"]
                cnt_before += df_before.shape[0]
                df_not_before = df[df["suffix_match"] != "['before']"]
                cnt_zero_in_degree_without_correlation = \
                    df_not_before[
                        df_not_before[
                            "cnt_vertexes_with_zero_indegree"] == 1].shape[0]
                cnt_zero_in_degree_with_correlation = \
                    df_not_before[
                        df_not_before[
                            "cnt_vertexes_with_zero_indegree"] > 1].shape[0]

                l = "{}" + ",{}" * 4 + "\n"
                l = l.format(metric,
                             cp_type,
                             cnt_before,
                             cnt_zero_in_degree_without_correlation,
                             cnt_zero_in_degree_with_correlation)
                f.write(l)


def basic_statistics_per_batch():
    out_path = "{}/prints/basic_statistics_per_batch.csv".format(script_dir)
    with open(out_path, "w") as f:
        f.write("str_dt,"
                "cnt_servers,"
                "cnt_valid_clients,"
                "cnt_clients\n")

        for str_dt in os.listdir("{}/prints".format(script_dir)):
            if os.path.isdir("{}/prints/{}".format(script_dir, str_dt)):
                servers = set()
                cnt_clients = 0
                cnt_valid_clients = 0

                in_path = ("{}/prints/{}/filtered/traceroute_per_mac.csv".
                           format(script_dir, str_dt))
                df = pd.read_csv(in_path)
                for _, row in df.iterrows():
                    cnt_clients += 1
                    for traceroute_type in \
                            unsupervised_utils.iter_traceroute_types():
                        valid_traceroute_field, traceroute_field = \
                            cp_utils.get_traceroute_fields(traceroute_type)

                        if (row["valid_cnt_samples"] and
                                row[valid_traceroute_field]):
                            servers.add(row["server"])
                            cnt_valid_clients += 1
                            break
                cnt_servers = len(servers)

                l = "{}" + ",{}" * 3 + "\n"
                l = l.format(str_dt,
                             cnt_servers,
                             cnt_valid_clients,
                             cnt_clients)
                f.write(l)


def statistics():
    problem_location_statistics()
    basic_statistics_per_batch()


if __name__ == "__main__":
    statistics()
