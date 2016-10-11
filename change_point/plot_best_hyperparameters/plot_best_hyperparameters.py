import os
import sys
import copy
import pymongo
from bson import json_util

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
from change_point.models.seg_neigh.seg_neigh import SegmentNeighbourhood
from change_point.models.sliding_windows.sliding_windows_online import \
    SlidingWindowsOnline
from change_point.models.sliding_windows.sliding_windows_offline import \
    SlidingWindowsOffline
from change_point.models.bayesian.bayesian_offline import BayesianOffline
from change_point.models.bayesian.bayesian_online import BayesianOnline
from change_point.models.hmm.gaussian_hmm import GaussianHMM
from change_point.models.hmm.discrete_hmm import DiscreteHMM
import change_point.utils.cmp_class as cmp_class
import change_point.utils.cmp_win as cmp_win


def create_dirs(dataset, model_class_name):
    for dir in ["{}/plots/".format(script_dir),
                "{}/plots/{}/".format(script_dir, dataset),
                "{}/plots/{}/{}/".format(script_dir, dataset,
                                         model_class_name)]:
        if not os.path.exists(dir):
            os.makedirs(dir)


def get_params(model_class_name, params):
    params_ret = copy.deepcopy(params)
    if ((model_class_name == SlidingWindowsOffline.__name__) or
            (model_class_name == SlidingWindowsOnline.__name__)):
        f_dist = getattr(cmp_win, params["f_dist"])
        params_ret["f_dist"] = f_dist
    return params_ret


def plot_best_hyperparameters():
    client = pymongo.MongoClient()

    collection = client["change_point"]["random_search"]
    model_classes = [SegmentNeighbourhood, SlidingWindowsOffline,
                     SlidingWindowsOnline, BayesianOffline, BayesianOnline,
                     GaussianHMM, DiscreteHMM]
    metric = cmp_class.f_1_score
    datasets = ["rosam@land.ufrj.br", "edmundo@land.ufrj.br"]

    metric = metric.__name__
    for dataset in datasets:
        for model_class in model_classes:
            cursor = collection.find({"$and": [{"dataset": dataset},
                                               {"model_class":
                                                model_class.__name__}]})
            cursor = cursor.sort("metrics.{}".format(metric),
                                 pymongo.DESCENDING).limit(1)
            for doc in cursor:
                cmp_class_args = doc["cmp_class_args"]
                preprocess_args = doc["preprocess_args"]
                params = get_params(doc["model_class"], doc["params"])

                create_dirs(dataset, model_class.__name__)
                out_dir_path = "{}/plots/{}/{}/".format(script_dir, dataset,
                                                        model_class.__name__)

                with open("{}/params.json".format(out_dir_path), "w") as f:
                    f.write(json_util.dumps(doc, indent=4, sort_keys=True))

                model = model_class(preprocess_args=preprocess_args, **params)
                model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    plot_best_hyperparameters()
