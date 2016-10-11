import os
import sys
import pandas as pd

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)


def is_valid_node(node, cnt_node):
    if type(node) != str:
        return False
    if " " in node:
        return False
    if len(node) < 4:
        return False
    if cnt_node < 3:
        return False
    return True


def print_valid_nodes():
    df = pd.read_csv("{}/input/probes_info.csv".format(base_dir), sep=" ")

    l = []
    for node in df["NODE"].unique():
        cnt_node = len(df[df["NODE"] == node])
        if is_valid_node(node, cnt_node):
            l.append((cnt_node, node))
    l.sort(reverse=True)

    with open("{}/prints/valid_nodes.csv".format(script_dir), "w") as f:
        f.write("node,cnt\n")
        for tp in l:
            f.write("{},{}\n".format(tp[1], tp[0]))


if __name__ == "__main__":
    print_valid_nodes()
