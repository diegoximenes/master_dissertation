import sys
import os
import datetime
import psycopg2
import psycopg2.extras

script_dir = os.path.join(os.path.dirname(__file__), ".")
base_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(base_dir)
import utils.dt_procedures as dt_procedures


def get_data():
    try:
        conn = psycopg2.connect("dbname='from_unsupervised_to_supervised' "
                                "user='postgres' host='localhost' "
                                "password='admin'")
        conn.autocommit = True
    except:
        print "unable to connect to the database"
        sys.exit(0)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT users.email, time_series.mac, time_series.server, "
                   "time_series.date_start, time_series.date_end, "
                   "change_points.change_points "
                   "FROM users, time_series, change_points "
                   "WHERE (change_points.id_user = users.id) AND "
                   "(change_points.id_time_series = time_series.id)")

    with open("classifications.csv", "w") as f:
        f.write("email,mac,server,dt_start,dt_end,change_points\n")
        for row in cursor.fetchall():
            if row["change_points"] == '':
                change_points = "\'\'"
            else:
                change_points = row["change_points"]
            dt_start = dt_procedures.from_js_strdate_to_dt(row["date_start"])
            dt_end = dt_procedures.from_js_strdate_to_dt(row["date_end"]) + \
                datetime.timedelta(days=1)
            f.write("{},{},{},{},{},\"{}\"\n".format(row["email"], row["mac"],
                                                     row["server"], dt_start,
                                                     dt_end, change_points))

if __name__ == "__main__":
    get_data()
