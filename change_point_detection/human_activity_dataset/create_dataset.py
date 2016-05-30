import numpy as np
import pandas as pd
import os

#created dataset info
min_number_of_segments = 1
max_number_of_segments = 30
min_segment_length = 30
number_of_time_series = 1000

#original dataset info
dataset_number_of_activities = 19
dataset_number_of_persons = 8
dataset_number_of_segments = 60
dataset_number_of_rows = 125
dataset_number_of_cols = 45

def read_data(in_dir, out_file, seg_id, activity, person, segment_id, segment_length, segment_start):
	file = open(in_dir + "/a" + str(activity).zfill(2) + "/p" + str(person) + "/s" + str(segment_id).zfill(2) + ".txt")
	lines = file.readlines()
	for i in range(segment_start, segment_start + segment_length): 
		is_change_point = "0"
		if seg_id != 0 and i == segment_start: is_change_point = "1"
		out_file.write(is_change_point + "," + lines[i])
	file.close()

def create_dataset(in_dir, out_dir):
	if os.path.exists(out_dir) == False: os.makedirs(out_dir)
	if os.path.exists(out_dir + "/dataset/") == False: os.makedirs(out_dir + "/dataset/")
	
	for ts_id in xrange(number_of_time_series): 
		last_activity, last_person = -1, -1
		out_file = open("./created_dataset/dataset/" + str(ts_id).zfill(4) + ".csv", "w")
		out_file.write("is_change_point")
		for i in range(dataset_number_of_cols): out_file.write("," + str(i))
		out_file.write("\n")

		number_of_segments = np.random.randint(min_number_of_segments, max_number_of_segments)
		seg_id = 0
		while seg_id < number_of_segments:
			activity = np.random.randint(1, dataset_number_of_activities)
			person = np.random.randint(1, dataset_number_of_persons)
			
			#avoid same segment in a row
			if (activity == last_activity) and (person == last_person): continue
			
			segment_id = np.random.randint(1, dataset_number_of_segments)
			segment_length = np.random.randint(min_segment_length, dataset_number_of_rows)
			segment_start = np.random.randint(0, dataset_number_of_rows - segment_length)
			
			read_data("./data/", out_file, seg_id, activity, person, segment_id, segment_length, segment_start)
				
			last_activity, last_person = activity, person
			
			#print "activity=" + str(activity) + ", person=" + str(person) + ", segment_id=" + str(segment_id) + ", segment_length=" + str(segment_length) + ", segment_start=" + str(segment_start)
			seg_id += 1
					
		print "ts_id=" + str(ts_id)
		out_file.close()	

create_dataset("./data", "./created_dataset")
