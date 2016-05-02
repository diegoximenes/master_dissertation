import sys

def get_uf_list(file_name):
	file = open(file_name)
	l = []
	for line in file: l.append(line.split()[-1])
	return list(set(l))

def get_entities_uf_dictionary(file_name):
	file = open(file_name)	
	dic = {}
	for line in file:
		entity, uf = line.split()[0], line.split()[1]
		dic[entity] = uf
	return dic

def get_entityType_id_uf():
	entityType_id_uf = {}
	entityType_id_uf["probe"] = get_entities_uf_dictionary("../input/probe_ufs.txt")
	entityType_id_uf["server"] = get_entities_uf_dictionary("../input/server_ufs.txt")
	return entityType_id_uf

def get_entityType_ufList():	
	entityType_ufList = {}
	entityType_ufList["probe"] = get_uf_list("../data_extractors/ufs/server_ufs.txt")
	entityType_ufList["server"] = get_uf_list("../data_extractors/ufs/probe_ufs.txt")
	return entityType_ufList

region_ufs = {}
region_ufs["north"] = ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]
region_ufs["northeast"] = ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]
region_ufs["central_west"] = ["GO", "MT", "MS", "DF"]
region_ufs["southeast"] = ["ES", "MG", "RJ", "SP"]
region_ufs["south"] = ["PR", "RS", "SC"]
