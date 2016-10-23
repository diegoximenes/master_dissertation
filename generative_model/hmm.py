import os
import sys
import datetime
import copy
import pandas as pd
import numpy as np

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_dir)
import utils.utils as utils
import utils.plot_procedures as plot_procedures
from utils.time_series import TimeSeries


class HMM():
    def unpack_row(self, row):
        dt_start = datetime.datetime.strptime(row["dt_start"], "%Y-%m-%d")
        dt_end = datetime.datetime.strptime(row["dt_end"], "%Y-%m-%d")
        in_path = utils.get_in_path(row["server"], row["mac"], dt_start,
                                    dt_end)
        ts = TimeSeries(in_path, "loss", dt_start, dt_end)
        return row["server"], row["mac"], dt_start, dt_end, ts

    def train(self):
        seqs = []
        df = pd.read_csv("{}/dataset/train.csv".format(script_dir))
        for idx, row in df.iterrows():
            _, _, _, _, ts = self.unpack_row(row)
            seqs.append(self.get_seq(ts))

        X = np.concatenate(seqs)
        lens = map(len, seqs)
        self.model.fit(X, lens)

    def test(self):
        df = pd.read_csv("{}/dataset/test.csv".format(script_dir))
        for idx, row in df.iterrows():
            server, mac, dt_start, dt_end, ts = self.unpack_row(row)
            seq = self.get_seq(ts)
            hidden_state_path = self.model.predict(seq)
            self.plot(server, mac, dt_start, dt_end, ts, hidden_state_path)

    def plot(self, server, mac, dt_start, dt_end, ts, hidden_state_path):
        ts_hidden_state_path = TimeSeries()
        ts_hidden_state_path.x = copy.deepcopy(ts.x)
        ts_hidden_state_path.y = copy.deepcopy(hidden_state_path)

        out_file_name = utils.get_out_file_name(server, mac, dt_start, dt_end)
        out_path = "{}/plots/{}/{}.png".format(script_dir,
                                               self.__class__.__name__,
                                               out_file_name)
        plot_procedures.plot_ts_share_x(ts, ts_hidden_state_path, out_path,
                                        compress=True,
                                        title1="raw time series",
                                        title2="best hidden state path",
                                        plot_type2="scatter",
                                        yticks2=range(self.model.n_components),
                                        ylim2=[-0.5,
                                               self.model.n_components - 0.5])

    def write_model(self, out_path):
        with open(out_path, "w") as f:
            f.write("hidden states\n")
            self.write_states(f)

            f.write("##########\n")
            f.write("hidden states start likelihood\n")
            for i in xrange(self.model.n_components):
                f.write("pi[{}]={}\n".format(i, self.model.startprob_[i]))

            f.write("##########\n")
            f.write("hidden states transition matrix\n")
            for i in xrange(self.model.n_components):
                for j in xrange(self.model.n_components):
                    f.write("a[{}][{}]={}\n".
                            format(i, j, self.model.transmat_[i][j]))

    def run(self):
        self.train()
        utils.create_dirs(["{}/plots/".format(script_dir),
                           "{}/plots/{}".format(script_dir,
                                                self.__class__.__name__)])
        self.write_model("{}/plots/{}/model.txt".
                         format(script_dir, self.__class__.__name__))
        self.test()
