import scipy.signal
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
        metric:
        dt_start: sao paulo datetime of the first day
        dt_end: sao paulo datetime of the last day
        ts_type: "raw", "hourly", "dist"
        compressed: boolean. If ts_type is "raw" then this parameter is
            irrelevant
        filters: list with filter application order
    """

    def __init__(self, in_path=None, metric=None, dt_start=None, dt_end=None,
                 ts_type="raw", compressed=False):
        self.x = []
        self.y = []
        self.metric = metric
        self.dt_start = dt_start
        self.dt_end = dt_end
        self.ts_type = ts_type
        self.compressed = compressed
        self.filters = []

        if (dt_start is not None) and (dt_end is not None):
            self.dt_start, self.dt_end = dt_start, dt_end

            if in_path is not None:
                self.read(in_path, metric)

                if compressed:
                    self.compress()

    def read(self, in_path, metric):
        raw_x, raw_y = read_input.get_raw(in_path, metric, self.dt_start,
                                          self.dt_end)

        if self.ts_type == "raw":
            self.x = raw_x
            self.y = raw_y
        elif self.ts_type == "hourly":
            self.x, self.y = self.get_hourly(raw_x, raw_y)

    def get_hourly(self, raw_x, raw_y):
        x = dt_procedures.generate_dt_list(self.dt_start, self.dt_end)

        dt_cntSum = {}
        for dt in x:
            dt_cntSum[dt] = [0, 0]

        for i in xrange(len(raw_x)):
            dt = raw_x[i]
            dt_rounded = datetime(dt.year, dt.month, dt.day, dt.hour)
            if dt_rounded not in dt_cntSum:
                continue
            dt_cntSum[dt_rounded][0] += 1
            dt_cntSum[dt_rounded][1] += raw_y[i]

        y = []
        for dt in x:
            if dt_cntSum[dt][0] > 0:
                y.append(float(dt_cntSum[dt][1]) / dt_cntSum[dt][0])
            else:
                y.append(None)

        return x, y

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

    def ma_smoothing(self, win_len):
        """
        centered window filter

        Arguments:
            win_len: must be odd integer
        """

        ret_x = []
        ret_y = []
        for i in xrange(win_len / 2, len(self.y) - win_len / 2):
            ysum, ycnt = 0, 0
            for j in xrange(i - win_len / 2, i + win_len / 2 + 1):
                if self.y[j] is not None:
                    ysum += self.y[j]
                    ycnt += 1
            if ycnt > 0:
                val = float(ysum) / ycnt
            else:
                val = None
            ret_x.append(self.x[i])
            ret_y.append(val)
        self.x = ret_x
        self.y = ret_y
        self.filters.append("ma_winlen{}".format(win_len))

    def percentile_filter(self, win_len, p):
        """
        centered window filter

        Arguments:
            win_len: must be odd integer
            p: must belong in [0.0, 1.0]
        """

        ret_x = []
        ret_y = []
        for i in xrange(win_len / 2, len(self.y) - win_len / 2):
            l = []
            for j in xrange(i - win_len / 2, i + win_len / 2 + 1):
                if self.y[j] is not None:
                    l.append(self.y[j])
            k = int(p * len(l))
            l = np.partition(l, k)
            ret_x.append(self.x[i])
            ret_y.append(l[k])
        self.x = ret_x
        self.y = ret_y
        self.filters.append("percentile_winlen{}_p{}".format(win_len, p))

    def savgol(self, win_len, poly_order):
        try:
            self.y = scipy.signal.savgol_filter(self.y, win_len, poly_order)
            self.filters.append("savgol_winlen{}_polyorder{}".
                                format(win_len, poly_order))
        except:
            pass

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
    return a TimeSeries with same dt_start, dt_end as the
    argument ts, but with other attributes empty
    """

    ts_ret = TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end, ts_type="dist")
    return ts_ret
