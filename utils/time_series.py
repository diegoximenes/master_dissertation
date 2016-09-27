import scipy.signal
import copy
import numpy as np
from datetime import datetime

import read_input
import dt_procedures


class TimeSeries:
    """
    univariate time series

    Attributes:
        x: sorted dt list
        y: mean values associated with x. Values can be None.
        raw_x:
        raw_y:
        dt_start: datetime of the first day
        dt_end: datetime of the last day
        ts_type: "raw", "hourly", "dist"
        compressed: boolean. If type is "raw" then this parameter is
            irrelevant
    """

    def __init__(self, in_path=None, metric=None, dt_start=None, dt_end=None,
                 ts_type="raw", compressed=False):
        self.x = []
        self.y = []
        self.raw_x = []
        self.raw_y = []
        self.dt_start = dt_start
        self.dt_end = dt_end
        self.ts_type = ts_type
        self.compressed = compressed

        if (dt_start is not None) and (dt_end is not None):
            self.dt_start, self.dt_end = dt_start, dt_end

            if in_path is not None:
                self.read(in_path, metric)

                if compressed:
                    self.compress()

    def read(self, in_path, metric):
        self.raw_x, self.raw_y = read_input.get_raw(in_path, metric,
                                                    self.dt_start, self.dt_end)

        if self.ts_type == "raw":
            self.x = copy.deepcopy(self.raw_x)
            self.y = copy.deepcopy(self.raw_y)
        elif self.ts_type == "hourly":
            self.x, self.y = self.get_hourly()

    def get_hourly(self):
        x = dt_procedures.generate_dt_list(self.dt_start, self.dt_end)

        dt_cntSum = {}
        for dt in x:
            dt_cntSum[dt] = [0, 0]

        for i in xrange(len(self.raw_x)):
            dt = self.raw_x[i]
            dt_rounded = datetime(dt.year, dt.month, dt.day, dt.hour)
            if dt_rounded not in dt_cntSum:
                continue
            dt_cntSum[dt_rounded][0] += 1
            dt_cntSum[dt_rounded][1] += self.raw_y[i]

        y = []
        for dt in x:
            if dt_cntSum[dt][0] > 0:
                y.append(float(dt_cntSum[dt][1]) / dt_cntSum[dt][0])
            else:
                y.append(None)

        return x, y

    def get_description(self):
        """
        returns a string describing ts
        """

        s = "dtstart{}_dtend{}_type{}_compressed{}".format(self.dt_start,
                                                           self.dt_end,
                                                           self.ts_type,
                                                           self.compressed)
        return s

    def compress(self):
        """
        remove None from time series
        """

        self.compressed = True
        ret_x, ret_y = [], []
        for i in range(len(self.y)):
            if self.y[i] is not None:
                ret_x.append(self.x[i])
                ret_y.append(self.y[i])
        self.x, self.y = ret_x, ret_y

    def ma_smoothing(self, win_len=11):
        """
        If y[t] == None this position is ignored on the computation
        """

        ret_y = []
        for i in xrange(len(self.y)):
            ysum, ycnt = 0, 0
            for j in xrange(max(0, i - win_len / 2),
                            min(len(self.y) - 1, i + win_len / 2) + 1):
                if self.y[j] is not None:
                    ysum += self.y[j]
                    ycnt += 1

            if ycnt > 0:
                val = float(ysum) / ycnt
            else:
                val = None
            ret_y.append(val)
        self.y = ret_y

    def percentile_filter(self, win_len, p):
        k = int((p - np.finfo(float).eps) * len(self.y))

        ret_y = []
        for i in xrange(len(self.y)):
            l = []
            for j in xrange(max(0, i - win_len / 2),
                            min(len(self.y) - 1, i + win_len / 2) + 1):
                if self.y[j] is not None:
                    l.append(self.y[j])
            k = min(k, len(l) - 1)
            l = np.partition(l, k)
            ret_y.append(l[k])
        self.y = ret_y

    def median_filter(self, win_len=3):
        """
        Args:
            win_len: must be odd
        """

        self.y = scipy.signal.medfilt(self.y, win_len)

    def savgol(self, win_len, poly_order):
        self.y = scipy.signal.savgol_filter(self.y, win_len, poly_order)

    def get_mean(self):
        """
        ignore None on the computation
        """

        sum, cnt = 0.0, 0
        for x in self.y:
            if x is not None:
                sum += x
                cnt += 1
        return sum / float(cnt)

    def get_variance(self):
        """
        ignore None on the computation
        """

        mean = self.get_mean()
        cnt_not_none = self.get_cnt_not_none()
        ret = - mean ** 2
        for x in self.y:
            if x is not None:
                ret += 1.0 / float(cnt_not_none) * (x ** 2)
        return ret

    def get_cnt_not_none(self):
        ret = 0
        for x in self.y:
            if x is not None:
                ret += 1
        return ret

    def get_acf(self, max_lag):
        if self.ts_type == "hourly":
            mean = self.get_mean()
            variance = self.get_variance()

            if np.isclose(variance, 0.0):
                return [], [], []

            lag_list = [0]
            acf_list = [1]
            cnt_pairs_list = [self.get_cnt_not_none()]
            for lag in xrange(1, max_lag + 1):
                cnt, sum = 0, 0.0
                for i in xrange(lag, len(self.y)):
                    if ((self.y[i] is not None) and
                            (self.y[i - lag] is not None)):
                        cnt += 1
                        sum += (self.y[i] - mean) * (self.y[i - lag] - mean)
                if cnt > 0:
                    lag_list.append(lag)
                    acf_list.append(1.0 / (float(cnt) * variance) * sum)
                    cnt_pairs_list.append(cnt)

            return lag_list, acf_list, cnt_pairs_list
        else:
            return [], [], []


def dist_ts(ts):
    """
    return a TimeSeries with same dt_start, dt_end, raw_x, raw_y as the
    argument, but with other attributes empty
    """

    ts_ret = TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end, ts_type="dist")
    ts_ret.raw_x = copy.deepcopy(ts.raw_x)
    ts_ret.raw_y = copy.deepcopy(ts.raw_y)
    return ts_ret
