import os
import sys
import datetime
import subprocess
import numpy as np
from functools import partial

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
import change_point.models.change_point_alg as change_point_alg
import change_point.cp_utils.cp_utils as cp_utils


class SegmentNeighbourhood(change_point_alg.ChangePointAlg):
    has_training = False

    def __init__(self, preprocess_args, metric, const_pen, f_pen, seg_model,
                 min_seg_len, max_cps):
        """
        Args:
            preprocess_args:
            metric:
            const_pen: penalization constant to be used in f_pen
            f_pen: penalization function wrt to (c_cps) number of change points
            seg_model: cost function to be used to asess segment homogeneity:
                       "Normal", "Exponential", "MSE"
            min_seg_len: minimum segment length
            max_cps: maximum number of change points in a time series
        """

        self.preprocess_args = preprocess_args
        self.metric = metric

        self.const_pen = const_pen
        self.f_pen = f_pen
        self.seg_model = seg_model
        self.min_seg_len = min_seg_len
        self.max_cps = max_cps

    def fit(self, df):
        pass

    def predict(self, ts):
        popen = subprocess.Popen(["{}/seg_neigh".format(script_dir),
                                  str(self.const_pen),
                                  self.f_pen,
                                  self.seg_model,
                                  str(self.min_seg_len),
                                  str(self.max_cps)],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        str_ts = "{}".format(len(ts.y))
        for v in ts.y:
            str_ts += "\n{}".format(v)
        str_cps, _ = popen.communicate(str_ts)

        cps = map(int, str_cps.split("\n")[:-1])

        return cps

    def plot(self, ts, ts_raw, correct, pred, conf, out_path):
        if "unsupervised" in out_path:
            ylabel = plot_procedures.get_default_ylabel(ts)
            plot_procedures.plot_ts(ts, out_path,
                                    dt_axvline=np.asarray(ts.x)[correct],
                                    ylabel=ylabel,
                                    xlabel="$i$",
                                    compress=True,
                                    title="median filtered")
        else:
            dt_axvline1 = np.asarray(ts.x)[correct]
            dt_axvline2 = np.asarray(ts.x)[pred]
            plot_procedures.plot_ts_share_x(ts_raw, ts, out_path,
                                            compress=False,
                                            title1="correct",
                                            dt_axvline1=dt_axvline1,
                                            dt_axvline2=dt_axvline2,
                                            title2="predicted. conf={}".
                                            format(conf),
                                            plot_type2="scatter")


def run(dataset, cmp_class_args, preprocess_args, param, metric):
    model = SegmentNeighbourhood(preprocess_args=preprocess_args,
                                 metric=metric, **param)

    utils.create_dirs(["{}/plots/".format(script_dir),
                       "{}/plots/{}/".format(script_dir, dataset),
                       "{}/plots/{}/{}".format(script_dir, dataset,
                                               metric)])
    out_dir_path = "{}/plots/{}/{}".format(script_dir, dataset, metric)
    model.plot_all(dataset, out_dir_path, cmp_class_args)


if __name__ == "__main__":
    # only used if RUN_MODE == specific_client
    server = "RIBDTCSRV03"
    mac = "64:66:B3:A6:BB:10"
    # only used if RUN_MODE == specific_client or RUN_MODE == single
    dt_start = datetime.datetime(2016, 5, 1)
    dt_end = datetime.datetime(2016, 5, 11)
    # used in all RUN_MODE
    cmp_class_args = {"win_len": 15}
    preprocess_args = {"filter_type": "percentile_filter",
                       "win_len": 13,
                       "p": 0.5}
    param = {"const_pen": 200,
             "f_pen": "n_cps",
             "seg_model": "Normal",
             "min_seg_len": 5,
             "max_cps": 4}
    metric = "latency"

    parallel_args = {"cmp_class_args": cmp_class_args,
                     "preprocess_args": preprocess_args, "param": param,
                     "metric": metric}
    sequential_args = parallel_args
    single_args = {"dt_start": dt_start, "dt_end": dt_end}
    single_args.update(parallel_args)
    specific_client_args = single_args
    fp_specific_client = partial(change_point_alg.run_specific_client,
                                 mac=mac, server=server,
                                 model_class=SegmentNeighbourhood,
                                 out_path=script_dir)
    cp_utils.parse_args(partial(change_point_alg.run_single, run=run),
                        single_args,
                        partial(change_point_alg.run_parallel, run=run),
                        parallel_args,
                        partial(change_point_alg.run_sequential, run=run),
                        sequential_args,
                        fp_specific_client,
                        specific_client_args)
