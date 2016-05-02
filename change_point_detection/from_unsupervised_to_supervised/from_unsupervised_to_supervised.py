import matplotlib, sys, os, ttk
import pandas as pd
import matplotlib.pylab as plt
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

if sys.version_info[0] < 3: import Tkinter as tk
else: import tkinter as tk

sys.path.append("../../import_scripts/")
import time_series, plot_procedures, datetime_procedures
from time_series import TimeSeries

#PARAMETERS
target_year, target_month = 2015, 12
metric = "loss"
bins_near_threshold = 5

date_dir = str(target_year) + "_" + str(target_month).zfill(2)

root = tk.Tk()
root.wm_title("From unsupervised to supervised")
#maximize window
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))

fig = Figure()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

#global variables of current probe
change_points = []
serverMac = ""
ts = ""
id_stringvar = tk.StringVar()

def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False

def handle_mouse_click(event):
	global ax, change_points
	if event.button == 1: 
		if is_number(event.xdata):
			ax.axvline(event.xdata, c = "red")
			change_points.append(event.xdata)
	elif event.button == 3:
		if len(change_points) > 0: 
			ax.lines.pop()
			change_points.pop()
	canvas.show()

def nearest_bin_present_in_ts(bin):
	strdt_bin = datetime_procedures.generate_hourly_bins_month([target_month, target_year])
	ret_bin = -1
	for strdt in ts.strdt_mean:
		if (ts.strdt_mean[strdt] != None) and (abs(strdt_bin[strdt] - bin) < abs(bin - ret_bin)):
			ret_bin = strdt_bin[strdt]
	if ret_bin < 0: return None
	return ret_bin	

def cp_too_near_to_another_cp(bin1, bin2):
	return abs(bin1 - bin2) <= bins_near_threshold
	
def save_change_points():
	global serverMac, change_points	
	server = serverMac.split("_")[0]
	mac = serverMac.split("_")[1]
	
	if os.path.exists("./output/") == False: os.makedirs("./output/")
	if os.path.exists("./output/" + date_dir) == False: os.makedirs("./output/" + date_dir)
	if os.path.exists("./output/" + date_dir + "/" + server) == False: os.makedirs("./output/" + date_dir + "/" + server)
	
	strdt_bin = datetime_procedures.generate_hourly_bins_month([target_month, target_year])
	bin_strdt = {}
	for strdt in strdt_bin: bin_strdt[strdt_bin[strdt]] = strdt
	
	change_points.sort()
			
	file = open("./output/" + date_dir + "/" + server + "/" + mac + ".csv", "w")
	file.write("bin,strdt\n")
	lastbin = None
	for cp in change_points: 
		bin = int(round(cp))
		bin = min(bin, max(bin_strdt))
		bin = max(bin, min(bin_strdt))
		bin = nearest_bin_present_in_ts(bin)

		if bin == None: continue
		if (lastbin != None) and (cp_too_near_to_another_cp(bin, lastbin)): continue
		file.write(str(bin) + "," + str(bin_strdt[bin]) + "\n")
		lastbin = bin
	file.close()
	
	change_points = []

server_mac_list = []
serverMac_id, id_serverMac = {}, {}
def read_macs():
	global server_mac_list, serverMac_id, id_serverMac
	for server in os.listdir("../input/" + date_dir):
		for file_name in os.listdir("../input/" + date_dir + "/" + server):
			mac = file_name.split(".")[0]
			server_mac_list.append([server, mac])
	server_mac_list.sort()
	for i in xrange(len(server_mac_list)): 
		serverMac = server_mac_list[i][0] + "_" + server_mac_list[i][1]
		serverMac_id[serverMac] = i
		id_serverMac[i] = serverMac
	 
combobox = ttk.Combobox(root, state = "readonly", width = 30)
def handle_combobox_selected(event):
	global serverMac, change_points
	save_change_points()
	serverMac = combobox.get()
	plot(serverMac)
def set_combobox():
	global combobox
	l = []
	for p in server_mac_list: l.append(p[0] + "_" + p[1])
	combobox["values"] = l
	combobox.bind("<<ComboboxSelected>>", handle_combobox_selected)
	combobox.pack()
	combobox.set(id_serverMac[0])

def plot():
	global ax, fig, serverMac, change_points, ts, label_text, serverMac_id
		
	id_stringvar.set(str(serverMac_id[serverMac] + 1) + "/" + str(len(serverMac_id)))
		
	server = serverMac.split("_")[0]
	mac = serverMac.split("_")[1]
	in_file_path = "../input/" + date_dir + "/" + server + "/" + mac + ".csv"
	in_file_path_cp = "./output/" + date_dir + "/" + server + "/" + mac + ".csv"

	strdt_axvline = set()
	if os.path.exists(in_file_path_cp):
		df = pd.read_csv(in_file_path_cp)
		for idx, row in df.iterrows():
			strdt_axvline.add(row["strdt"])
			change_points.append(int(row["bin"]))

	fig.clf()
	ax = fig.add_subplot(111)

	ts = TimeSeries(in_file_path, target_month, target_year, metric)
	plot_procedures.plotax_ts(ax, ts, strdt_axvline = strdt_axvline, ylim = [-0.01, 1.01])
	canvas.show()
	fig.canvas.mpl_connect('button_press_event', handle_mouse_click)

def next_button():
	global change_points, serverMac
	save_change_points()
	id = serverMac_id[serverMac]
	if id+1 in id_serverMac:
		combobox.set(id_serverMac[id+1])
		serverMac = id_serverMac[id+1]
		plot()	
					
def previous_button():
	global change_points, serverMac
	save_change_points()
	id = serverMac_id[serverMac]
	if id-1 in id_serverMac:
		combobox.set(id_serverMac[id-1])
		serverMac = id_serverMac[id-1]
		plot()	

read_macs()
set_combobox()
serverMac = id_serverMac[0]
plot()

button_previous = tk.Button(master=root, text='Previous', command = previous_button)
button_next = tk.Button(master=root, text='Next', command = next_button)
button_previous.pack(side=tk.BOTTOM)
button_next.pack(side=tk.BOTTOM)

tk.Label(root, textvariable = id_stringvar).pack()

root.mainloop()
