import os, shutil, math

frac_trainTest_train = 0.8
frac_trainTest_test = 0.2
frac_trainValidationTest_train = 0.6
frac_trainValidationTest_validation = 0.2
frac_trainValidationTest_test = 0.2

def split(in_dir, out_dir):
	file_name_list = []
	for file_name in os.listdir(in_dir): 
		if ".csv" in file_name:
			file_name_list.append(file_name)
	file_name_list.sort()
	
	if os.path.exists(out_dir + "/train_test/"): shutil.rmtree(out_dir + "/train_test/")
	os.makedirs(out_dir + "/train_test/")
	os.makedirs(out_dir + "/train_test/train")
	os.makedirs(out_dir + "/train_test/test")
	lim_train = int(math.ceil(frac_trainTest_train*len(file_name_list)))
	for i in range(lim_train): shutil.copy(in_dir + "/" + file_name_list[i], out_dir + "/train_test/train/" + file_name_list[i]) 
	lim_test = lim_train + int(math.ceil(frac_trainTest_test*len(file_name_list)))
	for i in range(lim_train, lim_test): shutil.copy(in_dir + "/" + file_name_list[i], out_dir + "/train_test/test/" + file_name_list[i]) 

	if os.path.exists(out_dir + "/train_validation_test/"): shutil.rmtree(out_dir + "/train_validation_test/")
	os.makedirs(out_dir + "/train_validation_test/train")
	os.makedirs(out_dir + "/train_validation_test/validation")
	os.makedirs(out_dir + "/train_validation_test/test")
	lim_train = int(math.ceil(frac_trainValidationTest_train*len(file_name_list)))
	for i in range(lim_train): shutil.copy(in_dir + "/" + file_name_list[i], out_dir + "/train_validation_test/train/" + file_name_list[i]) 
	lim_validation = lim_train + int(math.ceil(frac_trainValidationTest_validation*len(file_name_list)))
	for i in range(lim_train, lim_validation): shutil.copy(in_dir + "/" + file_name_list[i], out_dir + "/train_validation_test/validation/" + file_name_list[i]) 
	lim_test = lim_validation + int(math.ceil(frac_trainValidationTest_test*len(file_name_list)))
	for i in range(lim_validation, lim_test): shutil.copy(in_dir + "/" + file_name_list[i], out_dir + "/train_validation_test/test/" + file_name_list[i]) 

split("./created_dataset/dataset/", "./created_dataset/")
