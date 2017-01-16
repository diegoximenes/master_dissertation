import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.utils as utils


def aggregate_first_hop_not_zero_indegree_vertex():
    out_path = ("{}/prints/problem_location_first_hop_not_zero_indegree_"
                "vertex.csv".format(script_dir))
    with open(out_path, "w") as f:
        f.write("metric,str_dt,server,cp_dt_start,cp_dt_end,cp_type,"
                "fraction_of_clients,cnt_clients,clients,problem_location\n")

        for str_dt in os.listdir("{}/prints".format(script_dir)):
            if os.path.isdir("{}/prints/{}".format(script_dir, str_dt)):
                for metric in os.listdir("{}/prints/{}/filtered".
                                         format(script_dir, str_dt)):
                    if metric == "graph":
                        continue

                    in_dir = "{}/prints/{}/filtered/{}/".format(script_dir,
                                                                str_dt, metric)
                    if os.path.isdir(in_dir):
                        in_path = ("{}/problem_location_first_hop_not_zero_"
                                   "indegree_vertex.csv".format(in_dir))

                        df = pd.read_csv(in_path)
                        for _, row in df.iterrows():
                            l_format = "{}" + ",{}" * 7 + ",\"{}\"" * 2 + "\n"
                            f.write(l_format.format(metric,
                                                    str_dt,
                                                    row["server"],
                                                    row["cp_dt_start"],
                                                    row["cp_dt_end"],
                                                    row["cp_type"],
                                                    row["fraction_of_clients"],
                                                    row["cnt_clients"],
                                                    row["clients"],
                                                    row["problem_location"]))

    utils.sort_csv_file(out_path, ["metric", "str_dt", "metric", "server"],
                        ascending=[True, True, True, True])


def aggregate_correlation():
    out_path = ("{}/prints/problem_location_zero_indegree_vertexes_"
                "correlation.csv".format(script_dir))
    with open(out_path, "w") as f:
        f.write("metric,str_dt,server,traceroute_type,cp_dt_start,cp_dt_end,"
                "cp_type,cnt_vertexes_with_zero_indegree,suffix_match,"
                "vertexes_with_zero_indegree\n")
        for str_dt in os.listdir("{}/prints".format(script_dir)):
            if os.path.isdir("{}/prints/{}".format(script_dir, str_dt)):
                for metric in os.listdir("{}/prints/{}/filtered".
                                         format(script_dir, str_dt)):
                    if metric == "graph":
                        continue

                    in_dir = "{}/prints/{}/filtered/{}/".format(script_dir,
                                                                str_dt, metric)
                    if os.path.isdir(in_dir):
                        in_path = ("{}/problem_location_zero_indegree_"
                                   "vertexes_correlation.csv".format(in_dir))
                        df = pd.read_csv(in_path)
                        for _, row in df.iterrows():
                            l = "{},{},{},{},{},{},{},{},\"{}\",\"{}\"\n"
                            l = l.format(
                                metric,
                                str_dt,
                                row["server"],
                                row["traceroute_type"],
                                row["cp_dt_start"],
                                row["cp_dt_end"],
                                row["cp_type"],
                                row["cnt_vertexes_with_zero_indegree"],
                                row["suffix_match"],
                                row["vertexes_with_zero_indegree"])
                            f.write(l)
    utils.sort_csv_file(out_path,
                        ["cnt_vertexes_with_zero_indegree", "metric", "str_dt",
                         "metric", "server"],
                        ascending=[False, True, True, True, True])


def aggregate():
    aggregate_first_hop_not_zero_indegree_vertex()
    aggregate_correlation()


if __name__ == "__main__":
    aggregate()
