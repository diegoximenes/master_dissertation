import os
import sys
import pymongo
import matplotlib.pylab as plt

base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)

script_dir = os.path.join(os.path.dirname(__file__), ".")

client = pymongo.MongoClient()
db = client["change_point_random_search"]

pen_range = (0, 1000)
collection = db["SegmentNeighbourhood"]
f_cost = "f1_score"


def main():
    cursor = collection.find({"params.pen": {"$gte": pen_range[0]},
                              "params.pen": {"$lte": pen_range[1]},
                              "f_cost": f_cost,
                              "cmp_class_args.win_len": 10})
    l = []
    for doc in cursor:
        l.append((doc["params"]["pen"], doc["score"]))
    l.sort()
    x, y = [], []
    for tp in l:
        x.append(tp[0])
        y.append(tp[1])

    plt.grid()
    plt.ylabel(f_cost)
    plt.xlabel("pen")
    plt.plot(x, y, marker="o", markersize=4)
    plt.savefig("{}/pen_score.png".format(script_dir))

if __name__ == "__main__":
    main()
