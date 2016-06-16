import subprocess
import os

target_year, target_month = 2015, 12

date_dir = str(target_year) + "_" + str(target_month).zfill(2)


def create_dirs(server):
    if not os.path.exists("./change_points/"):
        os.makedirs("./change_points/")
    if not os.path.exists("./change_points/%s" % date_dir):
        os.makedirs("./change_points/" % date_dir)
    if not os.path.exists("./change_points/%s/%s" % (date_dir, server)):
        os.makedirs("./change_points/%s/%s" % (date_dir, server))


def get_change_points():
    cnt = 0
    for server in os.listdir("./input/%s" % date_dir):
        print server
        create_dirs(server)
        for file_name in os.listdir("./input/%s/%s" % (date_dir, server)):
            cnt += 1
            print "cnt=" + str(cnt)
            print file_name
            subprocess.call(["/usr/bin/Rscript", "./changepoint.r",
                             "./input/%s/%s/%s" % (date_dir, server,
                                                   file_name),
                             "./change_points/%s/%s/%s" % (date_dir, server,
                                                           file_name)])

get_change_points()
