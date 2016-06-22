import read_input
import copy
import scipy.signal


class TimeSeries:
    """
    - description: by now univariate time series
    - attributes:
        - dt_mean: mean of hourly dt of specified period
        - x: sorted hourly dt of specified period
        - y: mean values associated with x
        - raw_x: sorted raw datetime
        - raw_y: value, according with raw_x
        - dt_start: datetime of the first day considered
        - dt_end: datetime of the last day considered
    """

    def __init__(self, in_path=None, metric=None, dt_start=None, dt_end=None):
        self.dt_mean = {}
        self.x = []
        self.y = []
        self.raw_x = []
        self.raw_y = []
        self.dt_start = None
        self.dt_end = None

        if (dt_start is not None) and (dt_end is not None):
            self.dt_start, self.dt_end = dt_start, dt_end

            if in_path is not None:
                self.read(in_path, metric)

    def read(self, in_path, metric):
        self.dt_mean = read_input.get_dt_mean(in_path, metric,
                                              self.dt_start, self.dt_end)
        ts = from_dic_to_list_ts(self.dt_mean)
        self.x = ts[0]
        self.y = ts[1]
        self.raw_x, self.raw_y = read_input.get_raw_data(in_path, metric,
                                                         self.dt_start,
                                                         self.dt_end)


def dist_ts(ts):
    """
    - description:
        - return a TimeSeries with same dt_start, dt_end as the argument, but
          with other attributes empty
    - arguments:
    - return:
    """

    return TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end)


def ma_smoothing_list(y, window_len):
    """
    - description: apply ma smoothing on arrays
    - argument:
        - y: if y[t] == None, than this position is
        ignored on the computation
        - window_len:
    - returns:
        - ret_y:
    """

    ret_y = []
    for i in xrange(len(y)):
        ysum, ycnt = 0, 0
        for j in range(max(0, i - window_len / 2),
                       min(len(y) - 1, i + window_len / 2) + 1):
            if y[j] is not None:
                ysum += y[j]
                ycnt += 1

        if ycnt > 0:
            val = float(ysum) / ycnt
        else:
            val = None
        ret_y.append(val)
    return ret_y


def ma_smoothing(ts, window_len=11):
    """
    - description:
        - apply centered smoothing moving average to raw and hourly time
        series.  Useful to check periodicity visually.
          Example: ts[t] = (ts[t-1] + ts[t] + ts[t+1])/3
    - argument:
        - ts:
        - window_len: must be odd
    - returns:
        - TimeSeries not compressed
    """

    ts_ret = TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end)

    # apply ma to hourly time series. Example:
    # y[t] = ((y[t-1] != None) * y[t-1] + (y[t] != None) * y[t] +
    #         (y[t-1] != None) * y[t+1]) / ((y[t-1] != None) +
    #                                       (y[t] != None) +
    #                                       (y[t+1] != None))
    ts_ret.x = copy.deepcopy(ts.x)
    ts_ret.y = ma_smoothing_list(ts.y, window_len)
    for i in xrange(len(ts_ret.x)):
        ts_ret.dt_mean[ts_ret.x[i]] = ts_ret.y[i]

    # apply ma to raw ts
    ts_ret.raw_x = copy.deepcopy(ts.raw_x)
    ts_ret.raw_y = ma_smoothing_list(ts_ret.raw_y, window_len)

    return ts_ret


def median_filter(ts, window_len=3):
    """
    - description: useful to remove outliers.
    - arguments:
    - returns:
    """

    ts_ret = TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end)

    ts_ret.x = copy.deepcopy(ts.x)
    ts_ret.y = scipy.signal.medfilt(ts.y, window_len)
    for i in xrange(len(ts_ret.x)):
        ts_ret.dt_mean[ts_ret.x[i]] = ts_ret.y[i]

    ts_ret.raw_x = copy.deepcopy(ts.raw_x)
    ts_ret.raw_y = scipy.signal.medfilt(ts.raw_y, window_len)

    return ts_ret


def get_compressed(ts):
    """
    - description:
        - remove None from time series
    - arguments:
    - returns:
        - TimeSeries compressed
    """

    ts_ret = TimeSeries(dt_start=ts.dt_start, dt_end=ts.dt_end)
    ts_ret.raw_x = list(ts.raw_x)
    ts_ret.raw_y = list(ts.raw_y)

    for i in range(len(ts.y)):
        if ts.y[i] is not None:
            ts_ret.x.append(ts.x[i])
            ts_ret.y.append(ts.y[i])
        ts_ret.dt_mean[ts.x[i]] = ts.y[i]
    return ts_ret


def from_dic_to_list_ts(dt_measure):
    """
    - description:
    - argument:
    - returns:
    """
    x, y = [], []
    for dt in sorted(list(dt_measure.keys())):
        x.append(dt)
        y.append(dt_measure[dt])
    return [x, y]
