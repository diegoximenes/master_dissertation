import os
import sys
import subprocess
import pandas as pd

base_dir = os.path.join(os.path.dirname(__file__), "../../..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures
from change_point.utils.cmp_class import conf_mat

script_dir = os.path.join(os.path.dirname(__file__), ".")


class SegmentNeighbourhood():
    def __init__(self, pen):
        self.pen = pen

    def fit(self, df):
        pass

    def predict(self, row):
        dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
        date_dir = "{}_{}".format(dt_start.year,
                                  str(dt_start.month).zfill(2))
        in_path = "{}/input/{}/{}/{}.csv".format(base_dir, date_dir,
                                                 row["server"], row["mac"])

        date_start_r = \
            dt_procedures.from_js_strdate_to_r_strdate(row["date_start"])
        date_end_r = \
            dt_procedures.from_js_strdate_to_r_strdate(row["date_end"])

        subprocess.call(["/usr/bin/Rscript",
                         "{}/changepoint.R".format(script_dir), in_path,
                         "{}/tmp_pred".format(script_dir), date_start_r,
                         date_end_r, str(self.pen)],
                        stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        df = pd.read_csv("{}/tmp_pred".format(script_dir))
        os.remove("{}/tmp_pred".format(script_dir))

        return sorted(df["id"].values)

    def score(self, df, cmp_class_args, f_cost):
        conf = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
        for idx, row in df.iterrows():
            pred = self.predict(row)
            if pd.isnull(row["change_points_ids"]):
                correct = []
            else:
                correct = sorted(map(int, row["change_points_ids"].split(",")))
            # print "pred={}".format(pred)
            # print "correct={}".format(correct)

            lconf = conf_mat(correct, pred, **cmp_class_args)
            for key in lconf.keys():
                conf[key] += lconf[key]

        return f_cost(conf), conf
