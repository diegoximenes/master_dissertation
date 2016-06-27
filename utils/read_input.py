import datetime
import pandas as pd

import dt_procedures


def get_hourly(in_path, metric, dt_start, dt_end):
    """
    returns a dic in which the keys are each hour of the target month and the
    value is the mean of the specified hour

    Returns:
        x: sorted dts
        y: values associated with x
        dic:
            key: datetime
            value: mean of measures in strdt bin
    """

    x = dt_procedures.generate_dt_list(dt_start, dt_end)

    dt_cntSum = {}
    for dt in x:
        dt_cntSum[dt] = [0, 0]

    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        dt = dt_procedures.from_strdt_to_dt(row["dt"])
        dt_rounded = datetime.datetime(dt.year, dt.month, dt.day, dt.hour)
        if dt_rounded not in dt_cntSum:
            continue

        dt_cntSum[dt_rounded][0] += 1
        dt_cntSum[dt_rounded][1] += row[metric]

    dt_mean = {}
    for dt in dt_cntSum:
        if dt_cntSum[dt][0] > 0:
            dt_mean[dt] = float(dt_cntSum[dt][1]) / dt_cntSum[dt][0]
        else:
            dt_mean[dt] = None

    y = []
    for dt in sorted(list(dt_mean.keys())):
        y.append(dt_mean[dt])

    return x, y


def get_raw(in_path, metric, dt_start, dt_end):
    """
    Returns:
        x: sorted datetimes
        y: values, according with raw_x
        dt_mean:
    """

    l = []
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        dt = dt_procedures.from_strdt_to_dt(row["dt"])
        if dt_procedures.in_dt_range(dt, dt_start, dt_end):
            l.append([dt, row[metric]])

    x, y = [], []
    l.sort()
    for p in l:
        x.append(p[0])
        y.append(p[1])

    return x, y
