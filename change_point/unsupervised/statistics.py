import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)


def statistics():
    out_path = "{}/prints/problem_location_statistics.csv".format(script_dir)
    with open(out_path, "w") as f:
        f.write("metric,"
                "cnt_before,"
                "cnt_zero_indegree_without_correlation,"
                "cnt_zero_indegree_with_correlation\n")

        for metric in ["latency", "loss", "throughput_up"]:
            in_path = ("{}/prints/"
                       "problem_location_first_hop_not_zero_indegree_vertex"
                       ".csv".format(script_dir))
            df = pd.read_csv(in_path)
            df = df[df["metric"] == metric]
            df_before = df[df["problem_location"] == "['before']"]
            cnt_before = df_before.shape[0]

            in_path = ("{}/prints/"
                       "problem_location_zero_indegree_vertexes_correlation"
                       ".csv".format(script_dir))
            df = pd.read_csv(in_path)
            df = df[df["metric"] == metric]
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

            l = "{}" + ",{}" * 3 + "\n"
            l = l.format(metric,
                         cnt_before,
                         cnt_zero_in_degree_without_correlation,
                         cnt_zero_in_degree_with_correlation)
            f.write(l)


if __name__ == "__main__":
    statistics()
