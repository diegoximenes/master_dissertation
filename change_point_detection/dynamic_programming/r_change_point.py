import subprocess, os

target_year, target_month = 2015, 12

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

def create_dirs(server):
	if os.path.exists("./change_points/") == False: os.makedirs("./change_points/")
	if os.path.exists("./change_points/" + date_dir) == False: os.makedirs("./change_points/" + date_dir)
	if os.path.exists("./change_points/"  + date_dir + "/" + server) == False: os.makedirs("./change_points/" + date_dir + "/" + server)

def get_change_points():
	cnt = 0
	for server in os.listdir("./input/" + date_dir + "/"):
		print server
		create_dirs(server)
		for file_name in os.listdir("./input/" + date_dir + "/" + server + "/"):
			cnt += 1
			print "cnt=" + str(cnt)
			print file_name
			#subprocess.call(["/usr/bin/Rscript", "./changepoint.r", "./input/2015_12/NHODTCSRV04/64:66:B3:A6:B5:2E.csv", "./test.txt"])
			subprocess.call(["/usr/bin/Rscript", "./changepoint.r", "./input/" + date_dir + "/" + server + "/" + file_name, "./change_points/" + date_dir + "/" + server + "/" + file_name])

get_change_points()
