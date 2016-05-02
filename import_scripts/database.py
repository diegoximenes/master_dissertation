import os
from pymongo import MongoClient

import datetime_procedures

metric_list = ["latency", "loss", "throughput_down", "throughput_up", "jitter", "num_bytes_up", "num_bytes_down"]

def get_data_spdatetime(cursor, mac_provider = None):
	metric_datetime_measure = {}
	for metric in metric_list: metric_datetime_measure[metric] = {}
	
	for doc in cursor:
		if ("_id" not in doc) or ("mac" not in doc["_id"]) or ("date" not in doc["_id"]): continue
		
		mac = doc["_id"]["mac"]
		if (mac_provider != None) and ((mac not in mac_provider) or (mac_provider[mac] != "NET")): continue
		dt = datetime_procedures.get_datetime_sp(str(doc["_id"]["date"]))

		#latency
		if ("rtt" in doc) and ("lat" in doc["rtt"]) and ("m" in doc["rtt"]["lat"]) and ("s" in doc["rtt"]["lat"]) and (float(doc["rtt"]["lat"]["m"]) > 0):
			latency = doc["rtt"]["lat"]["m"]
			metric_datetime_measure["latency"][dt] = latency
			
		#loss
		if ("rtt" in doc) and ("loss" in doc["rtt"]):
			loss = float(doc["rtt"]["loss"])
			if loss > 0 and loss <= 1: metric_datetime_measure["loss"][dt] = loss
			elif loss == 0:
				if ("lat" in doc["rtt"]) and ("s" in doc["rtt"]["lat"]):
					metric_datetime_measure["loss"][dt] = loss
		
		#throughput down
		if ("thr" in doc) and ("tcp" in doc["thr"]) and ("down" in doc["thr"]["tcp"]) and ("v" in doc["thr"]["tcp"]["down"]):
			throughput_down = doc["thr"]["tcp"]["down"]["v"]
			metric_datetime_measure["throughput_down"][dt] = throughput_down
		
		#throughput up
		if ("thr" in doc) and ("tcp" in doc["thr"]) and ("up" in doc["thr"]["tcp"]) and ("v" in doc["thr"]["tcp"]["up"]):
			throughput_up = doc["thr"]["tcp"]["up"]["v"]
			metric_datetime_measure["throughput_up"][dt] = throughput_up

		#jitter
		if ("rtt" in doc) and ("jit" in doc["rtt"]) and ("m" in doc["rtt"]["jit"]):
			jitter = doc["rtt"]["jit"]["m"]
			metric_datetime_measure["jitter"][dt] = jitter
		
		#num_bytes_up
		if ("bytes" in doc) and ("u" in doc["bytes"]):
			num_bytes_up = doc["bytes"]["u"]
			metric_datetime_measure["num_bytes_up"][dt] = num_bytes_up

		#num_bytes_down
		if ("bytes" in doc) and ("d" in doc["bytes"]):
			num_bytes_down = doc["bytes"]["d"]
			metric_datetime_measure["num_bytes_down"][dt] = num_bytes_down

	return metric_datetime_measure

def get_data_spdatetime_per_mac(cursor, mac_provider = None):
	mac_metric_datetime_measure = {}
	
	for doc in cursor:
		if ("_id" not in doc) or ("mac" not in doc["_id"]) or ("date" not in doc["_id"]): continue

		mac = doc["_id"]["mac"]
		if (mac_provider != None) and ((mac not in mac_provider) or (mac_provider[mac] != "NET")): continue
		dt = datetime_procedures.get_datetime_sp(str(doc["_id"]["date"]))
	
		if mac not in mac_metric_datetime_measure: 
			mac_metric_datetime_measure[mac] = {}	
			for metric in metric_list: mac_metric_datetime_measure[mac][metric] = {}

		#latency
		if ("rtt" in doc) and ("lat" in doc["rtt"]) and ("m" in doc["rtt"]["lat"]) and ("s" in doc["rtt"]["lat"]) and (float(doc["rtt"]["lat"]["m"]) > 0):
			latency = doc["rtt"]["lat"]["m"]
			mac_metric_datetime_measure[mac]["latency"][dt] = latency
			
		#loss
		if ("rtt" in doc) and ("loss" in doc["rtt"]):
			loss = float(doc["rtt"]["loss"])
			if loss > 0 and loss <= 1: mac_metric_datetime_measure[mac]["loss"][dt] = loss
			elif loss == 0:
				if ("lat" in doc["rtt"]) and ("s" in doc["rtt"]["lat"]):
					mac_metric_datetime_measure[mac]["loss"][dt] = loss

		#throughput down
		if ("thr" in doc) and ("tcp" in doc["thr"]) and ("down" in doc["thr"]["tcp"]) and ("v" in doc["thr"]["tcp"]["down"]):
			throughput_down = doc["thr"]["tcp"]["down"]["v"]
			mac_metric_datetime_measure[mac]["throughput_down"][dt] = throughput_down
		
		#throughput up
		if ("thr" in doc) and ("tcp" in doc["thr"]) and ("up" in doc["thr"]["tcp"]) and ("v" in doc["thr"]["tcp"]["up"]):
			throughput_up = doc["thr"]["tcp"]["up"]["v"]
			mac_metric_datetime_measure[mac]["throughput_up"][dt] = throughput_up

		#jitter
		if ("rtt" in doc) and ("jit" in doc["rtt"]) and ("m" in doc["rtt"]["jit"]):
			jitter = doc["rtt"]["jit"]["m"]
			mac_metric_datetime_measure[mac]["jitter"][dt] = jitter
		
		#num_bytes_up
		if ("bytes" in doc) and ("u" in doc["bytes"]):
			num_bytes_up = doc["bytes"]["u"]
			mac_metric_datetime_measure[mac]["num_bytes_up"][dt] = num_bytes_up

		#num_bytes_down
		if ("bytes" in doc) and ("d" in doc["bytes"]):
			num_bytes_down = doc["bytes"]["d"]
			mac_metric_datetime_measure[mac]["num_bytes_down"][dt] = num_bytes_down

	return mac_metric_datetime_measure

def get_data_to_file(cursor, out_path):
	server_mac_dtMeasuresUf = {}
		
	cnt = 0
	for doc in cursor:
		cnt += 1
		print cnt

		if ("_id" not in doc) or ("mac" not in doc["_id"]) or ("date" not in doc["_id"]): continue
		if ("host" not in doc) or ("carrier" not in doc) or ("uf" not in doc) or ("huf" not in doc): continue
		
		if doc["carrier"] != "NET": continue
		if doc["uf"] != doc["huf"]: continue
	
		if ("rtt" not in doc) or ("loss" not in doc["rtt"]) or ("lat" not in doc["rtt"]) or ("xtrf" not in doc["rtt"]) or ("u" not in doc["rtt"]["xtrf"]) or ("d" not in doc["rtt"]["xtrf"]): continue

		loss = float(doc["rtt"]["loss"])
		if (loss < 0) or (loss > 1): continue
		if (loss < 1) and ("s" not in doc["rtt"]["lat"]): continue
	
		latency = doc["rtt"]["lat"]["m"]
		bytes_cross_traffic_down = doc["rtt"]["xtrf"]["d"]
		bytes_cross_traffic_up = doc["rtt"]["xtrf"]["u"]
		uf = doc["uf"]	
		host = doc["host"]
		mac = doc["_id"]["mac"]
		dt = datetime_procedures.get_datetime_sp(str(doc["_id"]["date"]))	
	
		print "dt=" + str(dt) + ", date=" + str(doc["_id"]["date"])
			
		if host not in server_mac_dtMeasuresUf: server_mac_dtMeasuresUf[host] = {}
		if mac not in server_mac_dtMeasuresUf[host]: server_mac_dtMeasuresUf[host][mac] = []
		server_mac_dtMeasuresUf[host][mac].append([dt, uf, loss, latency, bytes_cross_traffic_down, bytes_cross_traffic_up])
	
	if os.path.exists(out_path) == False: os.makedirs(out_path)
	for server in server_mac_dtMeasuresUf:
		if os.path.exists(out_path + "/" + server) == False: os.makedirs(out_path + "/" + server)

		for mac in server_mac_dtMeasuresUf[server]:
			server_mac_dtMeasuresUf[server][mac].sort()

			file = open(out_path + "/" + server + "/" + mac + ".csv", "w")
			file.write("uf,dt,loss,latency,num_bytes_cross_traffic_down,num_bytes_cross_traffic_up\n")
			for t in server_mac_dtMeasuresUf[server][mac]: file.write(str(t[1]) + "," + str(t[0]) + "," + str(t[2]) + "," + str(t[3]) + "," + str(t[4]) + "," + str(t[5]) + "\n")
			file.close()

