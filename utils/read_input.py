import pandas as pd

import dt_procedures


def get_raw(in_path, metric, dt_start, dt_end):
    """
    Returns:
        x: sorted datetimes
        y: values, according with raw_x
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
