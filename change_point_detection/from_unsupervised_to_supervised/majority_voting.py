import os
import sys
import datetime
import pandas as pd

sys.path.append("../../import_scripts/")
import dt_procedures
import plot_procedures
from time_series import TimeSeries

metric = "loss"


def get_datetime(strdt_js):
    strdate = strdt_js.split("T")[0]
    strtime = strdt_js.split("T")[1].split(".000")[0]
    dt = datetime.datetime(int(strdate.split("-")[0]),
                           int(strdate.split("-")[1]),
                           int(strdate.split("-")[2]),
                           int(strtime.split(":")[0]),
                           int(strtime.split(":")[1]),
                           int(strtime.split(":")[2]))
    dt_sp = dt_procedures.from_utc_to_sp(dt)
    dt_ret = datetime.datetime(dt_sp.year, dt_sp.month, dt_sp.day, dt_sp.hour,
                               dt_sp.minute, dt_sp.second)
    return dt_ret


def create_dirs(mac, server, date_start, date_end):
    dirs = ["./majority_voting/",
            ("./majority_voting/mac_{}_server{}_datestart{}_dateend{}".
             format(mac, server, date_start.replace("/", "-"),
                    date_end.replace("/", "-")))]
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
    return dirs[-1]


def update_classification_out(idx_classified_in_iteration, n_users,
                              min_fraction_of_votes, classification_out, l):
    if float(len(idx_classified_in_iteration)) / n_users >= \
            min_fraction_of_votes:
        classification_out.append(l[0][0])

    l_next = []
    for j in range(len(l)):
        if j not in idx_classified_in_iteration:
            l_next.append(l[j])
    return l_next


def majority_voting(tp, email_classificationDts_list):
    delta = 10
    min_fraction_of_votes = 0.5

    mac, server, date_start, date_end = tp[0], tp[1], tp[2], tp[3]
    dt_start = datetime.datetime(int(date_start.split("-")[2]),
                                 int(date_start.split("-")[0]),
                                 int(date_start.split("-")[1]))
    dt_end = datetime.datetime(int(date_end.split("-")[2]),
                               int(date_end.split("-")[0]),
                               int(date_end.split("-")[1]))
    in_path = "../input/{}_{}/{}/{}.csv".format(dt_start.year,
                                                str(dt_start.month).zfill(2),
                                                server, mac)
    ts = TimeSeries(in_path, metric, dt_start=dt_start, dt_end=dt_end)

    # transform classifications_dt in classifications_id
    dt_id, id_dt = {}, {}
    for i in xrange(len(ts.x)):
        dt_id[ts.x[i]] = i
        id_dt[i] = ts.x[i]
    email_classificationIds_list = []
    for p in email_classificationDts_list:
        email, class_dt = p[0], p[1]
        class_ids = []
        for dt in class_dt:
            class_ids.append(dt_id[dt])
        email_classificationIds_list.append([email, class_ids])

    l = []
    for p in email_classificationIds_list:
        for id in p[1]:
            l.append([id, p[0]])
    l.sort()

    # by now only get the left point
    classification_out = []
    n_users = len(email_classificationIds_list)
    while len(l) > 0:
        idx_classified_in_iteration = set()
        users_classified_in_iteration = set()
        idx_classified_in_iteration.add(0)
        users_classified_in_iteration.add(l[0][1])

        # print l
        solved_iteration = False
        for i in xrange(1, len(l)):
            if l[i][0] - l[0][0] > delta:
                l = update_classification_out(idx_classified_in_iteration,
                                              n_users,
                                              min_fraction_of_votes,
                                              classification_out,
                                              l)
                solved_iteration = True
                break
            else:
                if l[i][1] not in users_classified_in_iteration:
                    idx_classified_in_iteration.add(i)
                    users_classified_in_iteration.add(l[i][1])

        if not solved_iteration:
            l = update_classification_out(idx_classified_in_iteration,
                                          n_users,
                                          min_fraction_of_votes,
                                          classification_out,
                                          l)

    out_path = create_dirs(mac, server, date_start, date_end)
    for p in email_classificationDts_list:
        plot_procedures.plot_ts(ts, "{}/user_{}.png".format(out_path, p[0]),
                                ylim=[-0.01, 1.01], dt_axvline=p[1],
                                compress=True)
    class_dt_out = []
    for id in classification_out:
        class_dt_out.append(id_dt[id])
    plot_procedures.plot_ts(ts, "{}/correct.png".format(out_path),
                            ylim=[-0.01, 1.01], dt_axvline=class_dt_out,
                            compress=True)

    return classification_out


def process():
    macServerDtstartDtend_emailClassifications = {}

    # get data
    df = pd.read_csv("./majority_voting_data.csv", sep=";")
    for idx, row in df.iterrows():
        dt_cps = []
        tp = (row["mac"], row["server"], row["date_start"].replace("/", "-"),
              row["date_end"].replace("/", "-"))
        if tp not in macServerDtstartDtend_emailClassifications:
            macServerDtstartDtend_emailClassifications[tp] = []
        if row["change_points"] != "\'\'":
            for strdt_js in row["change_points"].split(","):
                if strdt_js != "":
                    dt = get_datetime(strdt_js)
                    dt_cps.append(dt)
        macServerDtstartDtend_emailClassifications[tp].append([row["email"],
                                                               dt_cps])

    macServerDtstartDtend_correctClassification = {}
    targets = [("64:66:B3:4F:FE:CE", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:7B:9B:B8", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:7B:A4:1C", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"),
               ("64:66:B3:50:00:1C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:50:00:3C", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:50:00:30", "CPDGDTCLDM14", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:50:06:82", "NHODTCSRV04", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:A6:9E:DE", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"),
               ("64:66:B3:A6:A9:16", "SPOTVTSRV16", "05-01-2016",
                "05-10-2016"),
               ("64:66:B3:A6:AE:76", "SNEDTCPROB01", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:A6:B3:B0", "SOODTCLDM24", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:A6:BC:D8", "SJCDTCSRV01", "05-11-2016",
                "05-20-2016"),
               ("64:66:B3:A6:A0:78", "AMRDTCPEV01", "05-01-2016",
                "05-10-2016")]

    for tp in targets:
        print tp
        macServerDtstartDtend_correctClassification[tp] = \
            majority_voting(tp, macServerDtstartDtend_emailClassifications[tp])

process()
