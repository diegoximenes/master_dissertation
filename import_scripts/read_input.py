import datetime
import pandas as pd

import dt_procedures


def get_dt_mean(in_path, metric, dt_start, dt_end):
    """
    - description:
        - returns a dic in which the keys are each hour of the target month
          and the value is the mean of the specified hour
    - arguments
    - returns:
        - dic:
            - key: datetime
            - value: mean of measures in strdt bin
    """

    dt_list = dt_procedures.generate_dt_list(dt_start, dt_end)

    dt_cntSum = {}
    for dt in dt_list:
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

    return dt_mean


def get_raw_data(in_path, metric, dt_start, dt_end):
    """
    - description:
    - arguments
    - returns:
        - raw_x: sorted datetimes
        - raw_y: values, according with raw_x
    """

    l = []
    df = pd.read_csv(in_path)
    for idx, row in df.iterrows():
        dt = dt_procedures.from_strdt_to_dt(row["dt"])
        if dt_procedures.in_dt_range(dt, dt_start, dt_end):
            l.append([dt, row[metric]])
    raw_x, raw_y = [], []
    l.sort()
    for p in l:
        raw_x.append(p[0])
        raw_y.append(p[1])
    return raw_x, raw_y
