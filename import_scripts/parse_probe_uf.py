def parse(in_file_name = "./probes_uf_sql_result.txt", out_file_name = "./input/ufs/probe_ufs.txt"):
	in_file = open(in_file_name)
	out_file = open(out_file_name, "w")
	lines = in_file.readlines()
	for i in range(3, len(lines)-2):
		mac = lines[i].split("|")[0].rstrip(" \n").lstrip(" \n")
		uf = lines[i].split("|")[1].rstrip(" \n").lstrip(" \n")
		out_file.write(mac + " " + uf + "\n")
	in_file.close()
	out_file.close()

parse()
