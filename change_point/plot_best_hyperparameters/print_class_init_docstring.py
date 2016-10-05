import os
import sys

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

script_dir = os.path.join(os.path.dirname(__file__), ".")


def print_class_init_docstring():
    model_classes = [SegmentNeighbourhood, SlidingWindowsOffline,
                     SlidingWindowsOnline, BayesianOnline,
                     GaussianHMM, DiscreteHMM]

    with open("{}/params_description.txt".format(script_dir), "w") as f:
        f.write("preprocess_args\n")
        f.write("   filter_type: none, ma_smothing\n")
        f.write("   win_len: window length used in filters\n")

        for model_class in model_classes:
            f.write("\n########################################\n")
            f.write("{}\n".format(model_class.__name__))
            f.write(model_class.__init__.__doc__)


if __name__ == "__main__":
    print_class_init_docstring()
