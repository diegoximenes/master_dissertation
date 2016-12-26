import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt
import numpy as np
from collections import defaultdict
from operator import itemgetter

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
import change_point.cp_utils.cp_utils as cp_utils
import change_point.unsupervised.unsupervised_utils as unsupervised_utils


def cmp_datasets(eps_hours):
    number_of_voters = 6

    tsid_cpdts = defaultdict(list)
    tsid_cnt = defaultdict(int)

    in_dir = "{}/change_point/input".format(base_dir)
    for dataset in os.listdir(in_dir):
        dataset_path = "{}/{}".format(in_dir, dataset)
        if (os.path.isdir(dataset_path) and
                ("unsupervised" not in dataset_path)):
            in_path = "{}/dataset.csv".format(dataset_path)

            df = pd.read_csv(in_path)
            for idx, row in df.iterrows():
                tsid_dic = {"server": row["server"],
                            "mac": row["mac"],
                            "dt_start": row["dt_start"],
                            "dt_end": row["dt_end"]}
                tsid = tuple(sorted(tsid_dic.items()))

                if row["change_points"] == "\'\'":
                    cp_dts = []
                else:
                    cp_dts = map(dt_procedures.from_js_strdt_to_dt,
                                 row["change_points"].split(","))
                    cp_dts = cp_utils.merge_close_cps(cp_dts, eps_hours)

                tsid_cpdts[tsid] += cp_dts
                tsid_cnt[tsid] += 1

    cnt_classific = 0
    cnt_classific_per_vote = []
    for tsid, cnt in tsid_cnt.iteritems():
        if cnt == number_of_voters:
            cnt_classific += 1
            tsid_dic = dict(tsid)
            l = map(lambda dt: {"dt": dt},
                    tsid_cpdts[tsid])
            l.sort(key=itemgetter("dt"))
            votes = unsupervised_utils.multiple_inexact_voting(l, eps_hours)

            for vote in votes:
                cnt_classific_per_vote.append(len(vote["interval"]))

    print "cnt_classfic={}".format(cnt_classific)
    print sorted(cnt_classific_per_vote)
    for i in xrange(1, number_of_voters + 1):
        print "p({})={}".format(i, cnt_classific_per_vote.count(i) /
                                float(len(cnt_classific_per_vote)))

    out_path = "{}/cnt_classifications_per_vote.png".format(script_dir)
    plt.clf()
    matplotlib.rcParams.update({"font.size": 27})
    plt.gcf().set_size_inches(16, 11)
    bins = range(1, max(cnt_classific_per_vote) + 2)
    weights = (np.asarray([1.0] * len(cnt_classific_per_vote)) /
               len(cnt_classific_per_vote))
    plt.ylabel("frequency")
    plt.xlabel("votes per change point")
    plt.xticks(bins[:-1])
    plt.hist(cnt_classific_per_vote, bins=bins, normed=True, weights=weights)
    plt.savefig(out_path)


if __name__ == "__main__":
    eps_hours = 4
    cmp_datasets(eps_hours)
